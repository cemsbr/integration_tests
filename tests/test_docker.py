"""Test connectivity between to hosts in Mininet."""
from unittest import TestCase

import pexpect

IMAGE = 'kytos/systests'
CONTAINER = 'kytos_tests'
PROMPT = 'root@.*:/usr/local/src/kytos# '
# Projects in install order
PROJECTS = 'python-openflow', 'kytos-utils', 'kytos'
NAPPS = 'kytos/of_core', 'kytos/of_l2ls'


class TestUbuntuRootRepoPing(TestCase):
    """As root, install the latest source code and test ping with mininet.

    This is not a regular test case because the tests (methods) are not
    self-contained. This is done to make them faster, easier to read and
    maintain. As Python unittest runs tests in alphabetical order, we force the
    order by using the pattern testNN_ in method names.
    """

    @classmethod
    def setUpClass(cls):
        """Launch tmux with 2 terminals inside docker."""
        cls._kytos = pexpect.spawn(
            f'docker run --rm -it --privileged --name {CONTAINER} {IMAGE}')
        cls._kytos.expect(PROMPT)
        cls._mininet = pexpect.spawn(
            f'docker exec -it --privileged {CONTAINER} /bin/bash')
        cls._mininet.expect(PROMPT)

    def test00_update_repositories(self):
        """Update all repositories."""
        self._kytos.sendline('kytos-update')
        self._kytos.expect(['Fast-forward', 'up-to-date'])

        self._kytos.expect(PROMPT)

    def test01_install_projects(self):
        """Install Kytos projects from cloned repository in safe order."""
        pip = 'pip install --no-index --find-links $KYTOSDEPSDIR .'
        for project in PROJECTS:
            self._kytos.sendline(f'cd $KYTOSDIR/{project}; {pip}; cd -')
            self._kytos.expect(f'Successfully installed .*{project}',
                               timeout=60)
            self._kytos.expect(PROMPT)

    def test02_launch_kytosd(self):
        """kytos-utils requires kytosd to be running."""
        self._kytos.sendline('kytosd -f')
        # Regex is for color codes
        self._kytos.expect(r'kytos \$> ')

    def test03_install_napps(self):
        """Install NApps for the ping to work.

        As self._kytos is blocked in kytosd shell, we use mininet terminal.
        """
        for napp in NAPPS:
            self._mininet.sendline(f'kytos napps install {napp}')
            self._mininet.expect('INFO    Enabled.')
            napp_name = napp.split('/')[0]
            self._kytos.expect(napp_name +'.+Running NApp')
            self._mininet.expect(PROMPT)

    def test04_launch_mininet(self):
        """Start mininet with OF 1.0 and Kytos as controller."""
        self._mininet.sendline(
            'mn --topo linear,2 --mac --controller=remote,ip=127.0.0.1'
            ' --switch ovsk,protocols=OpenFlow10')
        self._mininet.expect('mininet> ')

    def test05_ping(self):
        """Ping 2 mininet hosts."""
        self._mininet.sendline('h1 ping -c 1 h2')
        self._mininet.expect('64 bytes from 10.0.0.2: icmp_seq=\d+ ttl=64'
                             r' time=\d+ ms')

    @classmethod
    def tearDownClass(cls):
        """Stop container."""
        bash = pexpect.spawn('/bin/bash')
        bash.sendline(f'docker container stop {CONTAINER} && exit')
        bash.expect(f'\r\n{CONTAINER}\r\n', timeout=120)
        bash.wait()


class TestArchRootPyPIInstall(TestCase):
    """As root, install Kytos from PyPI using pip in Archlinux.

    This test reproduces kytos#465.
    """

    _shell = None
    _PROMPT = r'\[root@.* /\]# '

    @classmethod
    def setUpClass(cls):
        """Start docker with a higher timeout for downloading the image."""
        cls._shell = pexpect.spawn('docker run --rm -it base/archlinux',
                                   timeout=90)

    def test_install(self):
        """Install latest pip and then kytos."""
        self._install_pip()
        self._shell.sendline('pip install kytos')
        i = self._shell.expect(['Successfully installed .*kytos',
                               self._PROMPT], timeout=90)
        self.assertEqual(0, i, "Couldn't install kytos:\n" +
                         self._shell.before.decode('utf-8'))

    @classmethod
    def _install_pip(cls):
        cls._shell.expect(cls._PROMPT)
        cls._shell.sendline('pacman -Sy --noconfirm python-pip')
        cls._shell.expect(cls._PROMPT, timeout=120)

    @classmethod
    def tearDownClass(cls):
        """Quit container and it will be deleted."""
        if cls._shell:
            cls._shell.sendline('exit')
