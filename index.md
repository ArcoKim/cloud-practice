# Cloud Practice

## 풀이 순서
1. VPC 생성
1. Bastion Server 생성
1. 관계형 데이터베이스 생성
1. EKS Cluster 생성
1. Secrets Manager Secret 생성
1. ECR Repository 생성
1. ECR Repository Push
1. EKS Node Group 생성
1. MySQL 데이터베이스 설정
1. EKS Cluster 연결
1. EKS Addon 설치
1. Stress App 배포
1. CI/CD Pipeline 생성
1. Product App 배포

## VPC 생성
1. "VPC 등"으로 VPC, Public Subnet, Private Subnet 등을 생성합니다.
1. Protected Subnet을 생성합니다.
1. Protected Subnet의 Route Table을 생성합니다.

## Bastion Server 생성
1. 보안그룹에서 TCP 2026을 허용합니다.
1. AdministratorAccess 정책을 가진 IAM Role을 생성하여 연결합니다.
1. 다음과 같은 사용자 데이터를 사용합니다.
    ```bash
    #!/bin/bash
    sed -i 's/#Port 22/Port 2026/' /etc/ssh/sshd_config
    systemctl restart sshd
    yum update -y
    yum install -y docker
    systemctl start docker
    systemctl enable docker
    usermod -a -G docker ec2-user
    curl -O https://s3.us-west-2.amazonaws.com/amazon-eks/1.34.2/2025-11-13/bin/linux/arm64/kubectl
    chmod +x ./kubectl
    mv ./kubectl /usr/local/bin/kubectl
    kubectl completion bash | tee /etc/bash_completion.d/kubectl > /dev/null
    curl -fsSL -o get_helm.sh https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3
    chmod 700 get_helm.sh
    ./get_helm.sh
    curl --silent --location "https://github.com/weaveworks/eksctl/releases/latest/download/eksctl_$(uname -s)_arm64.tar.gz" | tar xz -C /tmp
    mv /tmp/eksctl /usr/local/bin
    ```
1. 탄력적 IP를 생성하여 인스턴스에 연결합니다.

## 관계형 데이터베이스 생성
1. 데이터베이스 보안그룹 생성 (TCP 3306)
1. 서브넷 그룹 생성 (Protected Subnet)
1. 데이터베이스 생성 - 다중 AZ DB 인스턴스 배포(인스턴스 2개)

## EKS Cluster 생성
1. 클러스터 생성 - 사용자 지정 구성 (자율 모드 사용 OFF)
1. 봉투 암호화 (자체 AWS KMS 키 사용)
1. 추가 보안그룹 생성 (TCP 443 - Bastion 보안그룹)
1. 클러스터 엔드포인트 액세스 선택 - 프라이빗
1. 컨트롤 플레인 로그 모두 ON (API 서버, 감사, Authenticator, 컨트롤러 관리자, 스케줄러)
1. 추가 기능 선택 (CoreDNS, kube-proxy, Amazon VPC CNI, 지표 서버)
1. 액세스 정책 추가 (Bastion Admin Role - AmazonEKSClusterAdminPolicy)

## Secrets Manager Secret 생성
1. /skills/app/product Secret 생성
    ``` json
    {"username":"admin","password":"Skill53##","engine":"mysql","host":"skills-rds-instance.cacgnhyyutg6.ap-northeast-2.rds.amazonaws.com","port":"3306","dbname":"dev"}
    ```

## ECR Repository 생성
1. product, stress Repository 생성
1. 이미지 태그 변경 가능성 : Immutable, 암호화 구성 : AWS KMS

## ECR Repository Push
1. 레지스트리 인증
    ``` bash
    aws ecr get-login-password --region ap-northeast-2 | docker login --username AWS --password-stdin 073813292468.dkr.ecr.ap-northeast-2.amazonaws.com
    ```
1. Builder 생성
    ``` bash
    docker buildx create --use --name multiarch
    ```
1. product 이미지 Push
    ``` bash
    docker buildx build --platform linux/amd64,linux/arm64 \
        -t 073813292468.dkr.ecr.ap-northeast-2.amazonaws.com/product:1 \
        --push .
    ```
1. stress 이미지 Push
    ``` bash
    docker buildx build --platform linux/amd64,linux/arm64 \
        -t 073813292468.dkr.ecr.ap-northeast-2.amazonaws.com/stress:1 \
        --push .
    ```

## EKS Node Group 생성
1. Addon (Name=skills-eks-addon-node), App (Name=skills-eks-app-node) 시작 템플릿 생성
1. Addon : 레이블 설정 (node=addon), App : 레이블, 테인트 설정 (node=app, NoSchedule)
1. AMI : Bottlerocket 사용

## MySQL 데이터베이스 설정
1. Bastion Host 접속 (VSCode, Terminal)
1. Table 생성, insert.sql을 통한 데이터 주입
    ``` bash
    sudo yum install -y mariadb105
    mysql -h skills-rds-instance.cacgnhyyutg6.ap-northeast-2.rds.amazonaws.com -P 3306 -u admin -p
    ```
    ``` sql
    USE dev;
    CREATE TABLE product (
        id VARCHAR(255),
        name VARCHAR(255) PRIMARY KEY
    );
    SOURCE /home/ec2-user/insert.sql;
    ```

## EKS Cluster 연결
1. Bastion Host 접속 (VSCode, Terminal)
1. kubeconfig 업데이트 및 환경변수 설정
    ``` bash
    aws configure

    echo "export CLUSTER_NAME=$(eksctl get clusters -o json | jq -r '.[0].Name')" >> ~/.bashrc
    echo "export AWS_DEFAULT_REGION=$(aws configure get region)" >> ~/.bashrc
    echo "export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)" >> ~/.bashrc
    source ~/.bashrc

    aws eks update-kubeconfig --name $CLUSTER_NAME
    ```

## EKS Addon 설치
1. skills Namespace 생성
1. AWS Load Balancer Controller 설치
1. External Secrets 설치 & Secrets Manager 연결
1. Cluster Autoscaler 설치
1. Pod Security Group 적용
    1. product 보안그룹 생성
    1. RDS 보안그룹 - product 보안그룹 허용
    1. product 보안그룹, 노드 보안그룹 각각 인바운드 추가
1. ArgoCD & ArgoCD Image Updater 설치
1. Fluent Bit 설치 & 구성

## Stress App 배포
``` bash
kubectl apply -f stress-config/
```

## CI/CD Pipeline 생성
1. Git 설정
    ``` bash
    sudo yum install -y git
    
    git config --global credential.helper '!aws codecommit credential-helper $@'
    git config --global credential.UseHttpPath true

    git config --global user.name $USER_NAME
    git config --global user.email $USER_EMAIL
    ```

1. product Repository 생성
    ``` bash
    git clone https://git-codecommit.ap-northeast-2.amazonaws.com/v1/repos/product

    cd product

    git add .
    git commit -m "first commit"
    git branch -M main
    git push origin main
    ```

1. product-config Repository 생성
    ``` bash
    git clone https://git-codecommit.ap-northeast-2.amazonaws.com/v1/repos/product-config

    cd product-config

    git add .
    git commit -m "first commit"
    git branch -M main
    git push origin main
    ```

1. CodeBuild 프로젝트 생성
    1. AmazonEC2ContainerRegistryPowerUser 권한 추가
1. CodePipeline 파이프라인 생성 (CodeCommit -> CodeBuild)

## Product App 배포
1. http://localhost:8080 접속 및 로그인
1. CONNECT REPO 진행
1. NEW APP 생성
1. SYNC POLICY > Automatic (Prune Resources, Self Heal)
1. ImageUpdater 배포