'''
로컬 개발 PC에서 원격 서버의 환경부터~운용까지 모든 세팅을 진행한다
'''
from fabric.contrib.files import append, exists, sed, put
from fabric.api import local, run, sudo, env
import os
import json


PROJECT_DIR = os.path.dirname(os.path.abspath(__file__) )
print(PROJECT_DIR)

envs = json.load( open( os.path.join(PROJECT_DIR, 'deploy.json') ) )
print(envs)
'''
{
'REPO_URL': 'https://github.com/widythj77/first', 
'PROJECT_NAME': 'first', 
'REMOTE_HOST': 'ec2-52-79-241-217.ap-northeast-2.compute.amazonaws.com', 
'REMOTE_HOST_SSH': '52.79.241.217', 
'REMOTE_USER': 'ubuntu'
}
'''
REPO_URL        = envs['REPO_URL']
PROJECT_NAME    = envs['PROJECT_NAME']
REMOTE_HOST     = envs['REMOTE_HOST']
REMOTE_HOST_SSH = envs['REMOTE_HOST_SSH']
REMOTE_USER     = envs['REMOTE_USER']

env.user = REMOTE_USER
env.hosts = [
    REMOTE_HOST_SSH,
]

env.use_ssh_config = True
env.key_filename   = 'first.pem'

project_folder = '/home/{}/{}'.format(env.user, PROJECT_NAME)
print(project_folder)

apt_requirements = [
    'curl',
    'git',
    'python3-pip',
    'python3-dev',
    'build-essential',
    'apache2',
    'libapache2-mod-wsgi-py3',
    'python3-setuptools',
    'libssl-dev',
    'libffi-dev',
]


'''
작성이 모두 끝난후
fab new_initServer
소스가 변경된 후
> fab update
'''

def new_initServer():
    _setup()
    update()

def _setup() :

    _init_apt()
    _install_apt_packages(apt_requirements)
    _makeing_virtualenv()



def _init_apt()
    yn = input('ubuntu linux update ok?:[y/n]')
    if cdyn =='y' : # 사용자가 업데이트를 원했다면
        # sudo => root권한으로 실행할때
        # sudo apt-get update
        # sudo apt-get upgrade
        sudo('apt=get update && apt-get -y upgrade')

def _install_apt_packages(requires) :
    reqs = ''
    for req in requires:
        #reqs = reqs + ' ' + req
        reqs += ' ' + req

sudo('apt-get -y install' +reqs )


def _making_virtualenv():
    if not exists('~/.virtualenvs'):


        run( 'mkdir ~/.virtualenvs' )
        sudo('pip3 install virtualenv virtualenvwrapper')
        cmd = '''
            "# python virtualenv global setting
            export WORKON_HOME=~/.virtualenvs
            # python location
            export VIRTUALENVWRAPPER_PYTHON="$(command /which python3)"
            # shell 실행
            source / usr/local/bin/virtualenvwrapper.sh"
        '''
        run('echo {} >> ~/.bashrc'.format(cmd ))


def update():
    _git_update()
    _virtualenv_update()
    _virtualhost_make()
    _grant_apache()
    _restart_apache()

def _git_update():
        if exists(project_folder + '/.git'): # 깃트가 존재하면
            # first 폴더로 이동 그리고 저장소로부터 fetch를 해서 최신 정보 가져온다
            run('cd %s && git fetch' % (project_folder,))
        else: # 깃트가 존재하지 않으면
            # 저장소로부터 최초로 프로젝트로 받아온다
            run('git clone %s %s' % (REPO_URL, project_folder))
            # 기트의 커밋된 로그를 최신으로 한개 가져온다 그것의 번호를 리턴
            # local: git log -n 1 --format=%H => 23847568413545
            current_commit = local("git log -n 1 --format=%H", capture=True)
            # first 폴더로 이동 그리고 git reset --hard  23847568413545
            # 최신 커밋사항으로 소스 반영
            run('cd %s && git reset --hard %s' % (project_folder, current_commit))

def _virtualenv_update():
    # /home/ubuntu/.virtualenvs/first 라는 가상환경 위치
    virtualenv_folder = project_folder + '/../.virtualenvs/{}'.format(PROJECT_NAME)

    # /home/ubuntu/.virtualenvs/first/bin/pip 가 존재하지 않으면
    if not exists(virtualenv_folder + '/bin/pip'):
        # /home/ubuntu/.virtualenvs로 이동하고 그리고
        # virtualenv first 가상환경 하나 생성
        run('cd /home/%s/.virtualenvs && virtualenv %s' % (env.user, PROJECT_NAME))

    # 상관없이 수행 => 필요한 python 모듈을 설치한다 (이 가상환경에게만 적용)
    #  /home/ubuntu/.virtualenvs/first/bin/pip install 
    #   -r/home/ubuntu/first/requirments/txt
    run('%s/bin/pip install -r %s/requirements.txt' % (
        virtualenv_folder, project_folder
    ))

def _ufw_allow():
    # ufw에서 80포트를 오픈
    sudo("ufw allow 'Apache Full'")
    # 리로드
    sudo("ufw reload")

def _virtualhost_make():
    script = """'
    <VirtualHost *:80>
    ServerName {servername}
    <Directory /home/{username}/{project_name}>
        <Files wsgi.py>
            Require all granted
        </Files>
    </Directory>
    WSGIDaemonProcess {project_name} python-home=/home/{username}/.virtualenvs/{project_name} python-path=/home/{username}/{project_name}
    WSGIProcessGroup {project_name}
    WSGIScriptAlias / /home/{username}/{project_name}/wsgi.py
    
    ErrorLog ${{APACHE_LOG_DIR}}/error.log
    CustomLog ${{APACHE_LOG_DIR}}/access.log combined
    
    </VirtualHost>'""".format(
        username=REMOTE_USER,
        project_name=PROJECT_NAME,
        servername=REMOTE_HOST,
    )
    # 아파치 사이트 목록 설정 파일에 first.conf 파일을 하나 생성해서 둔다
    sudo('echo {} > /etc/apache2/sites-available/{}.conf'.format(script, PROJECT_NAME))
    # 반영
    sudo('a2ensite {}.conf'.format(PROJECT_NAME))

def _grant_apache():

    sudo('chown -R :www-data ~/{}'.format(PROJECT_NAME))
    sudo('chmod -R 775 ~/{}'.format(PROJECT_NAME))

def _restart_apache():
    sudo('service apache2 restart')