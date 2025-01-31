.. _quipucords: https://github.com/quipucords/quipucords
.. _qpc: https://copr.fedorainfracloud.org/coprs/g/quipucords/qpc/
.. _sphinx: http://www.sphinx-doc.org/en/master/

=======
Camayoc
=======

A GPL-licensed Python library that facilitates functional testing of quipucords_.

.. image:: https://github.com/quipucords/camayoc/actions/workflows/tests.yml/badge.svg?branch=master
   :target: https://github.com/quipucords/camayoc/actions/workflows/tests.yml?query=branch%3Amaster
.. image:: https://codecov.io/gh/quipucords/camayoc/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/quipucords/camayoc


Installation
^^^^^^^^^^^^

Camayoc supports Python 3.9 and above, so it is recommended that you
install Camayoc into a virtual environment. There are several tools available
for managing virtual environments.

Some resources to learn about virtual environments:

* https://docs.python.org/3/tutorial/venv.html
* http://docs.python-guide.org/en/latest/dev/virtualenvs/


This is a suggested install method:

1. Clone the repo and navigate to the base directory::

    git clone https://github.com/quipucords/camayoc.git
    cd camayoc

2. Create and activate a Python3 virtual environment::

    python3 -m venv ~/envs/camayoc
    source ~/envs/camayoc/bin/activate

3. Install using make targets::

    # To install for development, install all dependencies
    make install-dev
    # If you only want to run the test suite, you can skip
    # a few dependencies with the plain "install" target
    make install

Configuration
^^^^^^^^^^^^^

Camayoc requires a configuration file to be installed to
``$XDG_CONFIG_HOME/camayoc/config.yaml``. On most systems this will be
``~/.config/camayoc/config.yaml``.

The config file tells Camayoc about the hosts you would like to run tests
against and the credentials to use with these hosts. It also tells Camayoc
where the quipucords_ server you want to test is running so the tests can
execute against the server.

Camayoc contains test suites for quipucords/qpc and quipucords/quipucords
projects. All portions of the test suite expect the same
config file format.  Any changes to the test suite that require changes to the
config file format should be made with this in mind.

There is an example annotated config file in ``example_config.yaml`` in
the root directory of the Camayoc repository.

Configuration Template
""""""""""""""""""""""

The Jenkins automation jobs often use a template configuration file when
running camaoyc. This template config has default values (such as
``${jenkins_ssh_file}``) that are swapped out for values which Jenkins
provides.  Additionally, ssh key files need to be set with the proper
permissions.

When working locally or in a dev environment, these steps can be automatically
configured with a template config using the ``configure-camayoc.yaml`` playbook
found in the ``camayoc/scripts/`` directory. To use the playbook, first open it
and set the variables at the top accordingly (or overwrite them when calling
the playbook using ``-e`` flags). Then, assuming the template configuration has
been downloaded and defined correctly in the playbook, run the playbook::

    cd scripts
    sudo ansible-playbook configure-camayoc.yaml



Configuring py.test
^^^^^^^^^^^^^^^^^^^

If you are testing machines that use ``https`` but do not have good
certificates, it can get difficult to read the test results due to warnings
about insecure connections. If this is a problem for you, an example
``pytest.ini`` file is provided in the root of the ``Camayoc`` repository that
disables these warnings. Additional configuration is possible through the
``pytest.ini`` file, these options are documented at
https://docs.pytest.org/en/latest/reference.html#ini-options-ref

For example, if you always want to run ``py.tests`` in verbose mode, this can
be done in the ``pytest.ini`` file.

Running The Test Suite
^^^^^^^^^^^^^^^^^^^^^^

Camayoc uses ``py.test`` as its test runner. The pytest project has excellent
documentation available at https://docs.pytest.org/en/latest/contents.html

Running Tests For quipucords_
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To run all the quipucords_ tests, first start the quipucords_ server
and set up your config file to point to the server. You should also
install the qpc_ executable in such a way that it is available in your
``$PATH``. Then run all API, CLI, and UI tests with::

    make test-qpc

.. warning::
    There are extra considerations you must take if you are running the
    quipucords server in a container.  First, your config file must use
    paths for sshkeys that exist on the server.
    Additionally you must map your ``/tmp`` directory to the server's ``/tmp``
    directory  because some tests create temporary files in ``/tmp`` that
    must be accessed by the server.


For UI tests, you should set the `SELENIUM_DRIVER` environment variable to either `Chrome`
or `Firefox` depending on what you want to use. If this is not set, UI tests are skipped. Additionally, you need to set up remote containers for use::

   # Chrome Selenium container, run as one line.
   docker run -d -P -p 4444:4444 --net="host" -v /dev/shm:/dev/shm \
   -v /tmp:/tmp:z selenium/standalone-chrome:3.14.0-arsenic

   # Firefox Selenium container
   docker run -d -P -p 4444:4444 --net="host" -v /dev/shm:/dev/shm \
   -v /tmp:/tmp:z selenium/standalone-firefox:3.14.0-arsenic

Additionally, you may want to observe the UI tests directly. In order to do so, you
need to use the debug versions of these remote containers, which provide a VNC server
on port 5900::

   # Chrome debug mode
   docker run -d -P -p 4444:4444 -p 5900:5900 --net="host" -v /dev/shm:/dev/shm \
   -v /tmp:/tmp:z selenium/standalone-chrome-debug:3.14.0-arsenic

   # Firefox debug mode
   docker run -d -P -p 4444:4444 -p 5900:5900 --net="host" -v /dev/shm:/dev/shm \
   -v /tmp:/tmp:z selenium/standalone-firefox-debug:3.14.0-arsenic

Ensure that the environment variable `SELENIUM_DEBUG` is set to `True`::

   export SELENIUM_DEBUG="True"

To observe tests as they run, use a VNC viewer. On Fedora, `vncviewer` is provided
by installing tigervnc. If the container is on localhost and port 5900, you can view the browser
with the following command::

   vncviewer :5900

There may be a password when using `vncviewer`, which by default is `secret`.
For more information on configuring debug mode, see https://github.com/SeleniumHQ/docker-selenium/#debugging.


To only test the API, CLI, or UI, you can take advantage of the
following make targets::

    # for API tests only
    make test-qpc-api
    # for CLI tests only
    make test-qpc-cli
    # for UI tests only
    make test-qpc-ui

Additionally you can select tests based on string matching. For
example, to run quipucords tests with ``create`` in the name and skip
any others, run::

    make test-qpc PYTEST_OPTIONS="--verbose -k create"

Any other valid pytest options may be included as well in this
variable.

By default scans defined in the config file are run at the beginning of the test session and results are cached to be used by other tests. This causes there to be some latency between when the test session begins and tests begin reporting results. If you want to run a test quickly without running the scans, you can include the environment variable ``RUN_SCANS=False`` in your ``py.test`` invocation. There is also a make target that provides this functionality::

    # Runs all tests except ones that require results of scanjobs

    make test-qpc-no-scans

    # You can do this manually as well
    # For example, if I just want to run a few login/logout
    # This would just run those without the scans running first.

    RUN_SCANS=False py.test camayoc/tests/qpc/api/v1/authentication/

Testing Camayoc
^^^^^^^^^^^^^^^
Testing Camayoc requires that you have installed the development dependencies. Do that by running ``make install-dev``.

To run all checks of the Camayoc test framework, including testing the docs
build, run::

    make all

The doc strings of each test case are designed to be digested by sphinx_. It is a good idea when writing new tests to make sure the doc strings are rendering as you expect them to. To make and serve the docs on your local machine::

    make docs-serve
