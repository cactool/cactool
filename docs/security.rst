Security
===================================

Password protecting user signup
--------------------------------------
To prevent external unkown users from creating accounts on the Cactool instance or to restrict account creation to authorised individuals, you can set up a signup authorisation code that requires users to enter a password before creating an account on the server instance.

By default, if no signup code is entered or the signup code provided is empty, no code will be required while creating an account on the server.

.. code-block:: json

  {
    "signup-code": "ENTER YOUR SIGNUP CODE HERE"
  }

Limiting file upload size
---------------------------------------
Strict file size upload limits can be set to prevent any service loss from any large files being sent over that the network or the server is unable to handle.

By default, the upload limit is 16 megabytes and if neccessary, the very strict default limit can be increased with no problem.

The example configuration below sets the file upload limit to 8 megabytes.

.. code-block:: json

  {
    "upload_size_limit": 8
  }



Using HTTPS
------------
You should use HTTPS when handling requests, this can easily be done through the use of applications that provide a reverse proxy such as `nginx <https://www.nginx.com/>`_ and `Apache <https://httpd.apache.org/>`_.

Do not modify the secret key
-----------------------------
Cactool automatically generates a 512 bit secret key when the server is first run. There is no need to modify this secret key to make it memorable as it is only used internally to cryptographically sign data and authenticate users. Shortening the secret key makes it guessable jeapardising the security of the server. 
