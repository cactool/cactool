List of configuration parameters
===================================

These can be set by running :code:`cactool set NAME VALUE` and retreived via :code:`cactool get NAME`

.. list-table::
  :widths: 25 15 60
  :header-rows: 1

  * - Parameter name
    - Type
    - Description

  * - port
    - Integer
    - The port the server should host itself on

  * - signup-code
    - String
    - The code needed to create an account on the cactool instance

  * - upload-limit
    - Integer
    - The maximum allowed size for uploaded files in megabytes

  * - max-rows
    - Integer
    - For machines with low amounts of RAM, the maximum number of dataset rows that are held in memory can be configured
