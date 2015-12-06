import argparse, os, sys, time, tutum

def set_env_var_for_service(service_name, verification_text):
    # verify tutum environment vars have been set
    user_name = os.environ.get('LETS_ENCRYPT_TUTUM_USER_NAME')
    password  = os.environ.get('LETS_ENCRYPT_TUTUM_PASSWORD')
    env_var   = os.environ.get('LETS_ENCRYPT_TUTUM_ENV_VAR_NAME')

    if user_name == None: raise ValueError('LETS_ENCRYPT_TUTUM_USER_NAME environment variable cannot be blank')
    if password  == None: raise ValueError('LETS_ENCRYPT_TUTUM_PASSWORD environment variable cannot be blank')
    if env_var   == None: raise ValueError('LETS_ENCRYPT_TUTUM_ENV_VAR_NAME environment variable cannot be blank')

    # authenticate
    # NOTE: would prefer to use api key, but it's not working on OSX in the current python-tutum incarnation (v0.20.2)
    tutum.auth.authenticate(user_name, password)

    # get desired service and set its env var
    services = tutum.Service.list()

    found_service = False
    for svc in services:
        if svc.name == service_name:
            found_service = True

            # make an api call to get all properties for the service.
            # this is necessary in order to get the service's env vars
            service = tutum.Service.fetch(svc.uuid)

            # set the env var
            found_env = False
            for index, item in enumerate(service.container_envvars):
                # update existing env var
                if item['key'] == env_var:
                    service.container_envvars[index]['value'] = verification_text

                    # alas, can't just update the env vars.  must first delete, then re-create
                    tmp_envvars = service.container_envvars

                    # clear env vars
                    service.container_envvars = []
                    if not service.save():
                        raise ValueError('error occurred while updating envvars for ' + service.name)

                    # clear env vars
                    service.container_envvars = tmp_envvars
                    if not service.save():
                        raise ValueError('error occurred while updating envvars for ' + service.name)

                    found_env = True
                    break # for index, item in enumerate(service.container_envvars)

            # create new env var if it doesn't exist
            if not found_env:
                # clone first item, change it, and append
                item = {'key': env_var, 'value': verification_text}
                service.container_envvars.append(item)

                # alas, can't just update the env vars.  must first delete, then re-create
                tmp_envvars = service.container_envvars

                # clear env vars
                service.container_envvars = []
                if not service.save():
                    raise ValueError('error occurred while updating envvars for ' + service.name)

                # re-create env vars
                service.container_envvars = tmp_envvars
                if not service.save():
                    raise ValueError('error occurred while updating envvars for ' + service.name)

            # finally, redeploy the service
            service.redeploy(reuse_volumes=True) # by default, the container volume will be reused

            # block until the redploy finishes
            finished = False

            sys.stderr.write('redeploying ' + service.name)
            sys.stderr.flush()
            num_wait_intervals = 10
            for i in range(0, num_wait_intervals):
                if i == num_wait_intervals - 1:
                    raise ValueError('tutum service redeployment exceeded the allowable time for: ' + service_name)

                sys.stderr.write('.')
                sys.stderr.flush()
                time.sleep(10)

                service = tutum.Service.fetch(service.uuid)
                finished = True if service.state == 'Running' else False

                if finished: break # for i in range(0, num_wait_intervals)

        if found_service: break # for svc in services

    # throw error if stack could not be found_env
    if not found_service: raise ValueError('could not find the following tutum service: ' + service_name)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="""\
Set an env var for the specified Tutum service with LetsEncrypt's simple http text.
The web server/service can then return the text when LetsEncrypt hits the
appropriate route during verification.

NOTE: YOU'LL NEED YOUR TUTUM USER NAME AND PASSWORD (NOT API KEY)

Prerequisites:
* python
* python-tutum

Example:
--------------
$ python tutum.py --service_name xxxx --verification_text xxxx
--------------

""")
    parser.add_argument("-svc", "--service-name",      required=True, help="the name of the tutum service to update")
    parser.add_argument("-ssl", "--verification_text", required=True, help="letsencrypt's simple http verification text to be hosted on the web server/service")

    args = parser.parse_args()
    set_env_var_for_service(args.service_name, args.verification_text)
    print "\nSuccess!"
