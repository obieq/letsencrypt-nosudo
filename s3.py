import boto, os, sys

def copy_verification_text(bucket_name, verification_text):
    aws_access_key_id     = os.environ.get('AWS_ACCESS_KEY_ID')
    aws_secret_access_key = os.environ.get('AWS_SECRET_ACCESS_KEY')

    if aws_access_key_id     == None: raise ValueError('AWS_ACCESS_KEY_ID environment variable cannot be blank')
    if aws_secret_access_key == None: raise ValueError('AWS_SECRET_ACCESS_KEY environment variable cannot be blank')

    conn = boto.connect_s3(aws_access_key_id, aws_secret_access_key)
    bucket = conn.get_bucket(bucket_name, validate=True)

    # parse "route name" from verification text
    file_name = verification_text.split('.')[0]

    # write verification text to file
    file = open(file_name, 'w')
    file.write(verification_text)
    file.close()

    # upload to bucket
    k = bucket.new_key('.well-known/acme-challenge/' + file_name)
    k.set_contents_from_filename(file_name)

    # cleanup
    os.remove(file_name)
