List of configuration parameters
===================================

These can be set by running :code:`cactool set NAME VALUE` and retreived via :code:`cactool get NAME`

.. list-table::
  :widths: 25 15 60
  :header-rows: 1

  * - Parameter name
    - Type
    - Description
    - Default

  * - port
    - Integer
    - The port the server should host itself on
    - 8080

  * - signup-code
    - String
    - The code needed to create an account on the cactool instance. If empty, no signup code is required
    -

  * - upload-limit
    - Integer
    - The maximum allowed size for uploaded files in megabytes
    - 1024

  * - request-email
    - Boolean
    - Whether users should be asked for an email on signup
    - true

  * - require-email
    - Boolean
    - Whether users should be forced to provide an email on signup
    - false

  * - email-domains
    - A list of Strings
    - A list containing email domains that can be used to sign up (e.g. :code:`["liverpool.ac.uk"]`). If this list is empty then any email is permitted to sign up.
    -

  * - require-2fa
    - Boolean
    - Whether user accounts require two-factor authentication
    - false

  * - instance-name
    - String
    - The name of the instance (e.g. The Univesity of Liverpool)
    -

  * - verify-emails
    - Boolean
    - Whether emails should be verified
    - true

  * - mail-server
    - Object
    - Login details for the mail server
