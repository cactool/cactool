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
    - The code needed to create an account on the cactool instance. If empty, no signup code is required

  * - upload-limit
    - Integer
    - The maximum allowed size for uploaded files in megabytes

  * - request-email
    - Boolean
    - Whether users should be asked for an email on signup

  * - require-email
    - Boolean
    - Whether users should be forced to provide an email on signup

  * - email-domains
    - A list of Strings
    - A list containing email domains that can be used to sign up (e.g. :code:`["liverpool.ac.uk"]`). If this list is empty then any email is permitted to sign up.

  * - instance-name
    - String
    - The name of the instance (e.g. The Univesity of Liverpool)
