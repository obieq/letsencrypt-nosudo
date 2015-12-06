import argparse, os, sys, time, tutum

def set_env_var_for_all_stack_services(user_name, password, stack_name, env_var, verification_text):
    print user_name
    print stack_name
    print env_var
    print verification_text

    # authenticate
    # NOTE: would prefer to use api key, but it's not working on OSX in the current python-tutum incarnation (v0.20.2)
    tutum.auth.authenticate(user_name, password)

    # get desired stack
    stacks = tutum.Stack.list()
    for stack in stacks:
        if stack.name == stack_name:
            # get the stack instance
            # stack = tutum.Stack.fetch(stack.uuid)
            # print stack.export()
            print stack.services

            # set the env var for each service
            # example of a stack.service value: /api/v1/service/2bc2e560-c660-48ff-b760-xxxxxxxxx/
            for stack_service in stack.services:
                service_uuid = stack_service.split('/')[4]
                service = tutum.Service.fetch(service_uuid)
                print service.name

                # set the env var
                found = False

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

                        found = True
                        break

                # create new env var if it doesn't exist
                if not found:
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

            # finally, redeploy the stack
            stack.redeploy() # by default, the container volume will be reused

            # block until the redploy finishes
            finished = False

            sys.stdout.write('redeploying ' + stack.name)
            sys.stdout.flush()
            while not finished:
                sys.stdout.write('.')
                sys.stdout.flush()
                time.sleep(10)
                stack = tutum.Stack.fetch(stack.uuid)
                finished = True if stack.state == 'Running' else False

            break

        # throw error if stack could not be found
        raise ValueError('could not find the following stack: ' + stack_name)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="""\
Set an env var for all services in a given Tutum stack with LetsEncrypt's simple http text.
All web servers/services in the stack can then return the text when LetsEncrypt hits the
appropriate route during verification.

NOTE: YOU'LL NEED YOUR TUTUM USER NAME AND PASSWORD (NOT API KEY)

Prerequisites:
* python
* python-tutum

Example:
--------------
$ python tutum.py --user-name your_tutum_username --password  your_tutum_passwword --stack_name xxxx --env_var xxxx --letsencrypt_simple_http_verification_text xxxx
--------------

""")
    parser.add_argument("-u",   "--user-name",         required=True, help="your tutum username")
    parser.add_argument("-p",   "--password",          required=True, help="your tutum password (api key not working in python-tutum v0.20.2)")
    parser.add_argument("-s",   "--stack-name",        required=True, help="the name of the tutum stack to update")
    # parser.add_argument("-svc", "--service-name", required=True, help="the name of the tutum service within the stack to update")
    parser.add_argument("-e",   "--env-var",           required=True, help="the name of the environment variable that will store the simple http verification text")
    parser.add_argument("-ssl", "--verification_text", required=True, help="letsencrypt's simple http verification text to be hosted on the web server/service")

    args = parser.parse_args()
    set_env_var_for_all_stack_services(args.user_name, args.password, args.stack_name, args.env_var, args.verification_text)
    print "\nSuccess!"