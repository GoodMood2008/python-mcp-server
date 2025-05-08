import requests
import os
import sys
# 获取当前目录的上一级目录 # 将上一级目录添加到PATH
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.join(current_dir, '..')
sys.path.insert(0, parent_dir)


os.environ.pop("http_proxy", None)  # 解决云桌面代理的问题，服务器或非外网代理可以不用
os.environ.pop("all_proxy", None)
os.environ.pop("https_proxy", None)

def _get_url(inf_type, func_name, logger):
    if inf_type == 'WSDL':
        return True, f'http://localhost:8080/queryWsdlMethod?name={func_name}'
    elif inf_type == 'YAML':
        return True, f'http://localhost:8080/queryYamlMethod?name={func_name}'
    elif inf_type == 'YAMLData':
        return True, f'http://localhost:8080/queryYamlData?name={func_name}'
    elif inf_type == 'CORBA':
        return True, f'http://localhost:8080/queryCorbaMethod?name={func_name}'
    elif inf_type == 'ASNData':
        return True, f'http://localhost:8080/queryAsnData?name={func_name}'
    else:
        msg = 'not valid interface type, type should be WSDL or YAML or CORBA or ASN'
        return False, msg

# inf_type: WSDL or YAML or CORBA or ASN
# func_name: 类名或者数据对象名
# is_need_recursive: 是否需要递归，通过这种方式减少知识量，加速AI推理速度
# 默认是True
def get_ops_inf(inf_type, func_name, logger = None, is_need_recursive = False):
    result, url = _get_url(inf_type, func_name, logger)
    if not result:
        return False, url
    if not is_need_recursive:
        url += '&needRecursive=false'
    logger.info('get url: ', url)
    headers = {
        "Content-Type": "text/plain"
    }
    try:
        # 创建一个会话对象
        response = requests.get(url)
        if response.status_code == 200:
            return True, response.text
        else:
            error = f"请求失败，状态码：{response.status_code}"
            logger.error(error)
            return False, error
    except Exception as e:
        error =  f"get {inf_type} {func_name} failed"
        logger.error(error)
        return False, error
