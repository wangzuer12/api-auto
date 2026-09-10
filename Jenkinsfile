pipeline {
    agent any

    triggers {
        // 轮询 SCM 兜底：每 3 分钟检查一次
        pollSCM('H/3 * * * *')
    }

    stages {
        stage('Checkout') {
            steps {
                git branch: 'main', url: 'https://github.com/wangzuer12/api-auto.git'
            }
        }

        stage('Install dependencies') {
            steps {
                sh 'python3 -m pip install -r requirements.txt'
            }
        }

        stage('Run API tests') {
            steps {
                sh 'python3 -m pytest tests/ --alluredir=allure-results'
            }
        }
    }

    post {
        always {
            allure includeProperties: false, results: [[path: 'allure-results']]
        }

        success {
            script {
                writeFile file: 'ding_msg.txt', text: """### ✅ API 自动化构建成功
- 项目：**${env.JOB_NAME}**
- 构建号：#${env.BUILD_NUMBER}
- 分支：`main`
- 耗时：${currentBuild.durationString}
- [查看 Allure 报告](${env.BUILD_URL}Allure_Report)
"""
                sendDingTalk()
            }
        }

        failure {
            script {
                writeFile file: 'ding_msg.txt', text: """### ❌ API 自动化构建失败
- 项目：**${env.JOB_NAME}**
- 构建号：#${env.BUILD_NUMBER}
- 分支：`main`
- 耗时：${currentBuild.durationString}
- [查看控制台日志](${env.BUILD_URL}console)
"""
                sendDingTalk()
            }
        }
    }
}

def sendDingTalk() {
    withCredentials([
        string(credentialsId: 'dingtalk-webhook', variable: 'https://oapi.dingtalk.com/robot/send?access_token=44c4337976a727e111c77cee7476cc692ca50011585993061689fd917efddc24'),
        string(credentialsId: 'dingtalk-secret', variable: 'SEC57cd5e521a8f9d6adbb4945266f557afdfe21e920281c9478e08b0e2e759c45a')
    ]) {
        sh 'python3 scripts/notify_dingtalk.py'
    }
}