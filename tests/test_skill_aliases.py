from nerajob.match import SKILL_ALIASES, expand_skills


def test_expand_skills_python_aliases():
    out = expand_skills({"python"})
    assert "django" in out
    assert "fastapi" in out
    assert "python" in out


def test_expand_skills_devops():
    out = expand_skills({"k8s"})
    assert "kubernetes" in out or "devops" in out
    assert SKILL_ALIASES


def test_expand_skills_rust_and_go():
    rust = expand_skills({"rust"})
    assert "cargo" in rust
    assert "tokio" in rust
    go = expand_skills({"golang"})
    assert "go" in go
    assert "gin" in go


def test_expand_skills_sql_and_cloud():
    sql = expand_skills({"postgres"})
    assert "sql" in sql
    assert "database" in sql
    cloud = expand_skills({"aws"})
    assert "cloud" in cloud
    assert "lambda" in cloud


def test_expand_skills_java_kotlin():
    java = expand_skills({"java"})
    assert "spring" in java
    assert "jvm" in java
    kotlin = expand_skills({"kotlin"})
    assert "java" in kotlin
    assert "maven" in kotlin


def test_expand_skills_mobile():
    mob = expand_skills({"flutter"})
    assert "mobile" in mob
    assert "android" in mob
    ios = expand_skills({"ios"})
    assert "mobile" in ios
    assert "swift" in ios


def test_expand_skills_education_and_edtech():
    lms = expand_skills({"lms"})
    assert "education" in lms
    assert "curriculum" in lms
    assert "assessment" in lms

    tutoring = expand_skills({"tutoring"})
    assert "edtech" in tutoring
    assert "learning management system" in tutoring
    assert "instructional design" in tutoring


def test_expand_skills_cloud_wave2():
    """Wave2: cloud aliases expanded with Azure/GCP services, IaC, serverless."""
    cloud = expand_skills({"cloud"})
    assert "aws" in cloud
    assert "gcp" in cloud
    assert "azure" in cloud
    assert "lambda" in cloud
    assert "cloudformation" in cloud
    assert "serverless" in cloud
    assert "pulumi" in cloud
    assert "gke" in cloud or "eks" in cloud
    assert "cdn" in cloud


def test_expand_skills_devops_wave2():
    """Wave2: devops aliases expanded with terraform, helm, sre, cicd tools."""
    devops = expand_skills({"devops"})
    assert "kubernetes" in devops
    assert "docker" in devops
    assert "terraform" in devops
    assert "helm" in devops
    assert "ansible" in devops
    assert "sre" in devops
    assert "prometheus" in devops
    assert "grafana" in devops
    assert "infrastructure as code" in devops or "iac" in devops


def test_expand_skills_mobile_wave2():
    """Wave2: mobile aliases expanded with cross-platform and native tooling."""
    mob = expand_skills({"mobile"})
    assert "flutter" in mob
    assert "react native" in mob
    assert "xamarin" in mob
    assert "maui" in mob
    assert "jetpack compose" in mob
    assert "xcode" in mob
    assert "android studio" in mob
    assert "pwa" in mob or "progressive web app" in mob


def test_expand_skills_finance_wave2():
    """Wave2: finance aliases expanded with payments, kyc, aml, quant, trading."""
    fin = expand_skills({"finance"})
    assert "fintech" in fin
    assert "payments" in fin
    assert "kyc" in fin
    assert "aml" in fin
    assert "quant" in fin
    assert "trading" in fin
    assert "plaid" in fin
    assert "payment gateway" in fin
    assert "wealth management" in fin
