import requests
from ReduceReuseRecycle import *
import traceback
import boto3
import re
import json

__token= None
s3 = boto3.client('s3')

def get_es_request(log, env, region_name, aplctn_cd, auth_type= None, key_index= None, headers ={}, params= {}, body= {}):
    """
    Perform API GET calls for Elastic Search
    :param log: basic logger
    :param env: environment string (ex dev, sit, prod)
    :param region_name: region on aws (ex us-east-1)
    :param aplctn_cd: Application code such as cii, aedl etc
    :param auth_type: Authentication Type such as basic/noauth/oauth2 etc
    :param key_index: Value which will be append to url
    :param headers: Headers for API call
    :param params: Params for API call
    :param body: Body for API call
    :return: JSON response
    """
    try:
        cert_path = get_certificate_path(log, env, region_name, aplctn_cd)
        if auth_type == 'basic':
            username, password, url = get_es_secrets(log, env, region_name, aplctn_cd, auth_type)
            url= url+key_index if key_index else url
            if cert_path:
                resp= requests.get(url, auth=(username, password), params=params, headers=headers, data=body, verify= cert_path)
            else:
                resp= requests.get(url, auth=(username, password), params=params, headers=headers, data=body, verify= False)
        else:
            url = get_es_secrets(log, env, region_name, aplctn_cd, auth_type)
            url= url+key_index if key_index else url
            if cert_path:
                resp= requests.get(url, params=params, headers=headers, data=body, verify= cert_path)
            else:
                resp= requests.get(url, params=params, headers=headers, data=body, verify= False)
        resp_json= {}
        if resp.text:
            resp_json= resp.json()
        if resp.status_code == 200:
            log.info('API call successful')
        else:
            log.info('API call failed')
            log.error(f'Invalid response {resp_json}!!!')
            raise InvalidStatus(
                f'Invalid response {resp_json}!!!')
        return resp_json
    except requests.exceptions.HTTPError as errh:
        log.critical('*** ERROR: Failed to perform get requests! ***')
        log.error(traceback.format_exc())
        raise errh
    except requests.exceptions.ConnectionError as errc:
        log.critical('*** ERROR: Failed to perform get requests! ***')
        log.error(traceback.format_exc())
        raise errc
    except requests.exceptions.Timeout as errt:
        log.critical('*** ERROR: Failed to perform get requests! ***')
        log.error(traceback.format_exc())
        raise errt
    except requests.exceptions.RequestException as err:
        log.critical('*** ERROR: Failed to perform get requests! ***')
        log.error(traceback.format_exc())
        raise err
    except Exception as error:
        log.critical('*** ERROR: Failed to perform get requests! ***')
        log.critical(traceback.format_exc())
        raise error

def post_es_request(log, env, region_name, aplctn_cd, auth_type= None, key_index= None, headers ={}, params= {}, body= {}):
    """
    Perform API POST calls for Elastic Search
    :param log: basic logger
    :param env: environment string (ex dev, sit, prod)
    :param region_name: region on aws (ex us-east-1)
    :param aplctn_cd: Application code such as cii, aedl etc
    :param auth_type: Authentication Type such as basic/noauth/oauth2 etc
    :param key_index: Value which will be append to url
    :param headers: Headers for API call
    :param params: Params for API call
    :param body: Body for API call
    :param verify_cert: By default True
    :return: JSON response
    """
    try:
        cert_path = get_certificate_path(log, env, region_name, aplctn_cd)
        if auth_type == 'basic':
            username, password, url = get_es_secrets(log, env, region_name, aplctn_cd, auth_type)
            url= url+key_index if key_index else url
            if cert_path:
                resp= requests.post(url, auth=(username, password), params=params, headers=headers, data=body, verify= cert_path)
            else:
                resp= requests.post(url, auth=(username, password), params=params, headers=headers, data=body, verify= False)
        else:
            url = get_es_secrets(log, env, region_name, aplctn_cd, auth_type)
            url= url+key_index if key_index else url
            if cert_path:
                resp= requests.post(url, params=params, headers=headers, data=body, verify= cert_path)
            else:
                resp= requests.post(url, params=params, headers=headers, data=body, verify= False)
        resp_json= {}
        if resp.text:
            resp_json= resp.json()
        if resp.status_code == 200:
            log.info('API call successful')
        else:
            log.info('API call failed')
            log.error(f'Invalid response {resp_json}!!!')
            raise InvalidStatus(
                f'Invalid response {resp_json}!!!')
        return resp_json
    except requests.exceptions.HTTPError as errh:
        log.critical('*** ERROR: Failed to perform post requests! ***')
        log.error(traceback.format_exc())
        raise errh
    except requests.exceptions.ConnectionError as errc:
        log.critical('*** ERROR: Failed to perform post requests! ***')
        log.error(traceback.format_exc())
        raise errc
    except requests.exceptions.Timeout as errt:
        log.critical('*** ERROR: Failed to perform post requests! ***')
        log.error(traceback.format_exc())
        raise errt
    except requests.exceptions.RequestException as err:
        log.critical('*** ERROR: Failed to perform post requests! ***')
        log.error(traceback.format_exc())
        raise err
    except Exception as error:
        log.critical('*** ERROR: Failed to perform post requests! ***')
        log.critical(traceback.format_exc())
        raise error

def get_es_secrets(log, env, region_name, aplctn_cd, auth_type):
    """
    Get the ES secrets from secret manager
    :param log: basic logger
    :param env: environment string (ex dev, sit, prod)
    :param region_name: region on aws (ex us-east-1)
    :param aplctn_cd: aplctn_cd such as edl, cii etc.
    :param auth_type: authentication type such as basic etc.
    :return: username, password and url
    """
    secret_name = f"{env}/es/{aplctn_cd}"
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )
    try:
        log.debug(secret_name)
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as error:
        secret_error_handling(log, error)
    else:
        if 'SecretString' in get_secret_value_response:
            secret = get_secret_value_response['SecretString']
        else:
            raise InvalidStatus("Unable to form connection")
    log.debug("Secrets successfully gathered from secretsmanager!")
    try:
        secret = json.loads(secret)
        if auth_type == 'basic':
            username = secret['username']
            password = secret[pw]
            url = secret['url']
            return username, password, url
        else:
            url = secret['url']
            return url
    except Exception as error:
        log.critical('*** ERROR: Unable to get the secrets! ***')
        log.critical(error)
        raise error

def get_token(log, env, region_name, aplctn_cd, auth_type, app_id, request, optional_args= {}):
    global __token
    try:
        prov_dict= request.get('provider')
        if prov_dict:
            prov_type= prov_dict['type']
            prov_url= prov_dict['url']
            prov_headers= prov_dict.get('headers', {})
            prov_body= prov_dict.get('body', {})
            prov_params= prov_dict.get('params', {})
            prov_req_type= prov_dict.get('request_type', 'post')
            prov_token= prov_dict.get('token')
            prov_params, prov_headers, prov_body, cert_path= get_api_secrets(log= log, env= env, region_name= region_name, aplctn_cd= aplctn_cd, auth_type= auth_type, provider= prov_type, app_id= app_id, headers= prov_headers, body= prov_body, params= prov_params)

            if prov_headers.get('Content-Type','') == 'application/json':
                prov_body = json.dumps(prov_body)

            if prov_req_type == 'post':
                if cert_path:
                    resp = requests.post(url= prov_url, params=prov_params, headers=prov_headers, data=prov_body, verify= cert_path, **optional_args)
                else:
                    resp = requests.post(url= prov_url, params=prov_params, headers=prov_headers, data=prov_body, verify= False, **optional_args)
            else:
                if cert_path:
                    resp = requests.get(url= prov_url, params=prov_params, headers=prov_headers, data=prov_body, verify= cert_path, **optional_args)
                else:
                    resp = requests.get(url= prov_url, params=prov_params, headers=prov_headers, data=prov_body, verify= False, **optional_args)
            if resp.status_code == 200:
                log.info('API Call authorization is successful')
                resp= resp.json()
                for i in prov_token:
                    __token= resp.get(i)
                    resp=resp.get(i)
            else:
                log.error('API Call authorization has failed')
                raise
            return __token
    except Exception as err:
        raise err


def get_api_request(log, env, region_name, aplctn_cd, request, response= {}, request_token = True, token_id = "None",optional_args= {}):
    """
    Perform API GET calls
    :param log: basic logger
    :param env: environment string (ex dev, sit, prod)
    :param region_name: region on aws (ex us-east-1)
    :param aplctn_cd: Application code such as cii, aedl etc
    :param request: api request with header, params, body.
    :param response: api response
    :return: JSON response
    """
    global __token
    try:

        auth_type= request.get('authentication')
        params= request.get('params')
        headers= request.get('headers')
        body= request.get('body')
        files= request.get('files')
        url= request.get('url')
        app_id= request.get('api_app_id')
        aplctn_cd= request.get('api_aplctn_cd',aplctn_cd)
        prov_type= 'na'

        if auth_type == 'oauth2' and request_token:
            __token = get_token(log, env, region_name, aplctn_cd, auth_type, app_id, request, optional_args)
        elif request_token == False:
            __token = token_id

        if __token:
            headers= json.loads(json.dumps(headers).replace('${token}',__token))

        cert_path= None
        if auth_type in ('api_key','oauth2','oauth1', 'basicauth'):
            params, headers, body, cert_path= get_api_secrets(log= log, env= env, region_name= region_name, aplctn_cd= aplctn_cd, auth_type= auth_type, provider= prov_type, app_id= app_id, headers= headers, body= body, params= params)

        verify= cert_path if cert_path else False
        if files:
            resp = requests.get(url, params=params, headers=headers, files=files, verify= verify, **optional_args)
        else:
            resp = requests.get(url, params=params, headers=headers, data=body, files=files, verify= verify, **optional_args)

        if resp.status_code == 200:
            log.info(f'API GET Request Call is successful with status code = {resp.status_code}')
        else:
            log.error(f'API call failed with api status_code = {resp.status_code} and api reason = {resp.reason}')
        return resp
    except requests.exceptions.HTTPError as errh:
        log.critical('*** ERROR: Failed to perform get requests! ***')
        log.error(traceback.format_exc())
        raise errh
    except requests.exceptions.ConnectionError as errc:
        log.critical('*** ERROR: Failed to perform get requests! ***')
        log.error(traceback.format_exc())
        raise errc
    except requests.exceptions.Timeout as errt:
        log.critical('*** ERROR: Failed to perform get requests! ***')
        log.error(traceback.format_exc())
        raise errt
    except requests.exceptions.RequestException as err:
        log.critical('*** ERROR: Failed to perform get requests! ***')
        log.error(traceback.format_exc())
        raise err
    except Exception as error:
        log.critical('*** ERROR: Failed to perform get requests! ***')
        log.critical(traceback.format_exc())
        raise error

def post_api_request(log, env, region_name, aplctn_cd, request, response= {}, request_token = True, token_id = "None",optional_args= {}):
    """
    Perform API POST calls
    :param log: basic logger
    :param env: environment string (ex dev, sit, prod)
    :param region_name: region on aws (ex us-east-1)
    :param aplctn_cd: Application code such as cii, aedl etc
    :param auth_type: Authentication Type such as basic/noauth/oauth2 etc
    :param key_index: Value which will be append to url
    :param headers: Headers for API call
    :param params: Params for API call
    :param body: Body for API call
    :return: JSON response
    """
    global __token
    try:
        auth_type= request.get('authentication')
        params= request.get('params')
        headers= request.get('headers')
        body= request.get('body')
        files= request.get('files')
        url= request.get('url')
        app_id= request.get('api_app_id')
        aplctn_cd= request.get('api_aplctn_cd',aplctn_cd)
        prov_type= 'na'
        if auth_type == 'oauth2' and request_token:
            __token = get_token(log, env, region_name, aplctn_cd, auth_type, app_id, request, optional_args)
        elif request_token == False:
            __token = token_id

        if __token:
            headers= json.loads(json.dumps(headers).replace('${token}',__token))

        cert_path= None
        if auth_type in ('api_key','oauth2','oauth1', 'basicauth'):
            params, headers, body, cert_path= get_api_secrets(log= log, env= env, region_name= region_name, aplctn_cd= aplctn_cd, auth_type= auth_type, provider= prov_type, app_id= app_id, headers= headers, body= body, params= params)

        if headers.get('Content-Type') !='application/x-www-form-urlencoded':
            body=json.dumps(body)

        verify= cert_path if cert_path else False
        if files:
            resp = requests.post(url, params=params, headers=headers, files=files, verify= verify, **optional_args)
        else:
            resp = requests.post(url, params=params, headers=headers, data=body, files=files, verify= verify, **optional_args)

        if resp.status_code == 200:
            log.info(f'API POST Request Call is successful with status code = {resp.status_code}')
        else:
            log.error(f'API call failed with api status_code = {resp.status_code} and api reason = {resp.reason}')
        return resp
    except requests.exceptions.HTTPError as errh:
        log.critical('*** ERROR: Failed to perform post requests! ***')
        log.error(traceback.format_exc())
        raise errh
    except requests.exceptions.ConnectionError as errc:
        log.critical('*** ERROR: Failed to perform post requests! ***')
        log.error(traceback.format_exc())
        raise errc
    except requests.exceptions.Timeout as errt:
        log.critical('*** ERROR: Failed to perform post requests! ***')
        log.error(traceback.format_exc())
        raise errt
    except requests.exceptions.RequestException as err:
        log.critical('*** ERROR: Failed to perform post requests! ***')
        log.error(traceback.format_exc())
        raise err
    except Exception as error:
        log.critical('*** ERROR: Failed to perform post requests! ***')
        log.critical(traceback.format_exc())
        raise error

def get_api_secrets(log, env, region_name, aplctn_cd, auth_type, provider, app_id, params= {}, headers= {}, body= {}):
    """
    Get the API secrets from secret manager
    :param log: basic logger
    :param region_name: region on aws (ex us-east-1)
    :param env: environment string (ex dev, sit, prod)
    :param aplctn_cd: aplctn_cd such as edl, cii etc.
    :param provider: OAuth2 provider can be PING etc.
    :return: username and password
    """
    aplctn_cd = aplctn_cd.lower()
    secret_name = f'{env}/api/{aplctn_cd}'
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )
    try:
        log.debug(secret_name)
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as error:
        secret_error_handling(log, error)
    else:
        if 'SecretString' in get_secret_value_response:
            secret = get_secret_value_response['SecretString']
        else:
            raise InvalidStatus("Unable to form connection")
    log.debug("Secrets successfully gathered from secretsmanager!")
    ssl_cert_path= None
    try:
        secret = json.loads(secret)
        params= override_api_dict(log= log, provider= provider, app_id= app_id, ip_dict= secret, op_dict= params, type='params')
        headers= override_api_dict(log= log, provider= provider, app_id= app_id, ip_dict= secret, op_dict= headers, type='header')
        body= override_api_dict(log= log, provider= provider, app_id= app_id, ip_dict= secret, op_dict= body, type='body')
        if auth_type == 'oauth2':
            ssl= secret.get(f'{provider}_{app_id}_ssl', 'false') if app_id and secret.get(f'{provider}_{app_id}_ssl') else secret.get(f'{provider}_ssl', 'false')
            if ssl == 'true':
                ssl_cert = secret.get(f'{provider}_{app_id}_ssl_cert') if app_id and secret.get(f'{provider}_{app_id}_ssl_cert') else secret.get(f'{provider}_ssl_cert')
                ssl_algo = secret.get(f'{provider}_{app_id}_ssl_algo') if app_id and secret.get(f'{provider}_{app_id}_ssl_algo') else secret.get(f'{provider}_ssl_algo')
                if ssl_algo:
                    ssl_cert= eval(f'{ssl_algo}(cert= ssl_cert)')
                ssl_cert_path= f'/tmp/{env}_api_{aplctn_cd}_{provider}_{auth_type}_cert.pem'
                download_cert(log, cert_path= ssl_cert_path, cert_val_lst= ssl_cert)
            return params, headers, body, ssl_cert_path
        elif auth_type == 'oauth1':
            #token= secret.get(f'{app_id}_token') if app_id and secret.get(f'{app_id}_token') else secret.get(f'token')
            ssl= secret.get(f'{app_id}_ssl', 'false') if app_id and secret.get(f'{app_id}_ssl') else secret.get(f'ssl', 'false')
            if ssl == 'true':
                ssl_cert = secret[f'ssl_cert']
                ssl_algo = secret.get(f"ssl_algo")
                if ssl_algo:
                    ssl_cert= eval(f'{ssl_algo}(cert= ssl_cert)')
                ssl_cert_path= f'/tmp/{env}_api_{aplctn_cd}_{auth_type}_cert.pem'
                download_cert(log, cert_path= ssl_cert_path, cert_val_lst= ssl_cert)
            return params, headers, body, ssl_cert_path
        elif auth_type =='api_key':
            #api_key= secret.get(f'{app_id}_api_key') if app_id and secret.get(f'{app_id}_api_key') else secret.get(f'api_key')
            ssl= secret.get(f'{app_id}_ssl', 'false') if app_id and secret.get(f'{app_id}_ssl') else secret.get(f'ssl', 'false')
            if ssl == 'true':
                ssl_cert = secret[f'ssl_cert']
                ssl_algo = secret.get(f"{provider}_ssl_algo")
                if ssl_algo:
                    ssl_cert= eval(f'{ssl_algo}(cert= ssl_cert)')
                ssl_cert_path= f'/tmp/{env}_api_{aplctn_cd}_{provider}_cert.pem'
                download_cert(log, cert_path= ssl_cert_path, cert_val_lst= ssl_cert)
            return params, headers, body, ssl_cert_path
        elif auth_type == "basicauth":
            import base64
            username= secret.get(f'{app_id}_username') if app_id and secret.get(f'{app_id}_username') else secret.get(f'username')
            password= secret.get(f'{app_id}_password') if app_id and secret.get(f'{app_id}_password') else secret.get(f'password')
            credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
            headers['Authorization'] = f"Basic {credentials}"
            return params, headers, body, ssl_cert_path
    except Exception as error:
        log.critical('*** ERROR: Unable to get the secrets! ***')
        log.critical(error)
        raise error

def get_certificate_path(log, env, region_name, aplctn_cd):
    """
    Get the certificate from secret manager
    :param log: basic logger
    :param region_name: region on aws (ex us-east-1)
    :param env: environment string (ex dev, sit, prod)
    :param aplctn_cd: aplctn_cd such as edl, cii etc.
    :param provider: OAuth2 provider can be PING etc.
    :return: username and password
    """
    secret_name = f'{env}/api/cert/{aplctn_cd}'
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )
    try:
        log.debug(secret_name)
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
        if 'SecretString' in get_secret_value_response:
            secret = get_secret_value_response['SecretString']
        else:
            raise InvalidStatus("Unable to form connection")
        log.debug("Secrets successfully gathered from secretsmanager!")
        cert_path= f'/tmp/api/cert/{aplctn_cd}.crt'
        download_cert(log, cert_path, secret)
        return cert_path
    except ClientError as error:
        return False

def download_cert(logger, cert_path, cert_val):
    try:
        file = open(cert_path, "w")
        file.write(cert_val)
        file.close()
    except Exception as error:
        logger.error(error)
        raise error

def override_api_dict(log, provider, app_id, ip_dict, op_dict, type):
    for i,j in op_dict.items():
        if isinstance(j, str) :
            jr = re.sub('[^_a-zA-Z0-9 \n\.]', '', j)
            if "$$" in j:
                if jr in ip_dict.keys():
                    op_dict[i]= ip_dict[jr]
                    log.info(f'*** {j} in request {type} is replaced with {jr} Key value from Secret manager.')
                elif f"{app_id}_{jr}" in ip_dict.keys():
                    op_dict[i] = ip_dict[f"{app_id}_{jr}"]
                    log.info(f'*** {j} in request {type} is replaced with {app_id}_{jr} Key value from Secret manager.')
                elif f"{provider}_{jr}" in ip_dict.keys():
                    op_dict[i] = ip_dict[f"{provider}_{jr}"]
                    log.info(f'*** {j} in request {type} is replaced with {provider}_{jr} Key value from Secret manager.')
                elif f"{app_id}_{provider}_{jr}" in ip_dict.keys():
                    op_dict[i] = ip_dict[f"{app_id}_{provider}_{jr}"]
                    log.info(f'*** {j} in request {type} is replaced with {app_id}_{provider}_{jr} Key value from Secret manager.')
            else:
                log.debug(f'*** {jr} is missing in ip_dict***')
        elif isinstance(j, dict):
            log.info(f'*** Iterate through Sub Dict ***')
            override_api_dict(log, provider, app_id, ip_dict, j, type)
    return op_dict

def verify_api_key(log, env, region_name, aplctn_cd, app_id, api_key):
    """
    Get the API key from secret manager
    :param log: basic logger
    :param region_name: region on aws (ex us-east-1)
    :param env: environment string (ex dev, sit, prod)
    :param aplctn_cd: aplctn_cd such as edl, cii etc.
    :param app_id: APP Id such as edw, cii etc
    :param api_key: API Key to verify.
    :return: dictionary with api key
    """
    secret_name = f'{env}/api/{aplctn_cd}'
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )
    try:
        log.debug(secret_name)
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as error:
        secret_error_handling(log, error)
    else:
        if 'SecretString' in get_secret_value_response:
            secret = get_secret_value_response['SecretString']
        else:
            raise InvalidStatus("Unable to form connection")
    log.debug("Secrets successfully gathered from secretsmanager!")
    try:
        secret = json.loads(secret)
        app_api_key = secret.get(f"{app_id}_api_key", secret.get("api_key"))
        if app_api_key != api_key:
            log.error(f'API Key Verify Failed ***')
            return False
        return True
    except Exception as error:
        log.error('*** ERROR: Unable to get the secrets! ***')
        log.error(error)
        raise error
