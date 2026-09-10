pipeline {
    agent any

    triggers {
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

// ↓↓↓ 关键改动：用 script 块包裹函数定义 ↓↓↓
script {
    def sendDingTalk() {
        withCredentials([
            string(credentialsId: 'dingtalk-qa', variable: 'DING_WEBHOOK'),
            string(credentialsId: 'dingtalk-qa-secret', variable: 'DING_SECRET')
        ]) {
            sh 'python3 scripts/notify_dingtalk.py'
        }
    }
}