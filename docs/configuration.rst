Basic configuration
===================================

The config.json file
----------------------
The :code:`config.jsosn` file allows for customisation of the Cactool web server and is automatically generated the first time the Cactool starts.

Manually writing out configurations for the config file isn't required as Cactool automatically sets reasonable defaults as values for each of the fields.

As an example, you could use to configuration file to specify that Cactool should runs on port number 8080

.. code-block:: json

  {
    "port": 8080 
  }

More information is given in the :ref:`Configuration <advanced-configuration>` section.
