==================================
Installation and Usage
===================================

Install instructions
=====================
Using pip
---------------------------
First install the latest version of Cactool using pip

.. code-block:: bash

    pip install -U cactool

Running Cactool
----------------
After performing these steps, you can start the Cactool server at any time by simply running :code:`cactool`. If that doesn't work, you may have to run Cactool by using :code:`python -m cactool`

Updating Cactool
-----------------
To update Cactool, simply run :code:`pip install -U cactool`

Using docker
-------------------------
Begin by cloning the Cactool GitHub repository.

.. code-block:: bash
   git clone https://github.com/cactool/cactol

Then start the Cactool server using :code:`docker-compose up`

.. code-block:: bash
    cd cactool
    docker-compose up -d
