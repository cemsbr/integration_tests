Kytos System Testing
====================

To be used by the core team to test Kytos in a virtual network. Requires docker.
Install the requirements.txt and run:

.. code-block:: bash

  # Only once, download the docker images:
  # docker pull kytos/systest
  # docker pull base/archlinux
  # All tests:
  python3.6 -m unittest discover -v tests
  # All tests of a file:
  python3.6 -m unittest -v tests/test_docker.py
  # A class:
  python3.6 -m unittest -v tests.test_docker.TestUbuntuRootRepoPing
  # One test only:
  python3.6 -m unittest -v tests.test_docker.TestUbuntuRootRepoPing.test01_install_projects
