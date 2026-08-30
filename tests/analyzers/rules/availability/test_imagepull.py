from datetime import datetime

import pytest

from kubesage.analyzers.rules.availability.imagepull import ImagePullRule
from kubesage.models.container import ContainerSnapshot
from kubesage.models.finding import ResourceRef
from kubesage.models.incident import Incident


@pytest.fixture
def imagepull_rule() -> ImagePullRule:
    return ImagePullRule()


def test_imagepull_rule_with_waiting_reason_imagepullbackoff(
    imagepull_rule: ImagePullRule,
) -> None:
    incident = Incident(
        namespace="test",
        pod="test",
        phase="Pending",
        observed_at=datetime.now(),
        containers=[
            ContainerSnapshot(
                name="test",
                image="test",
                ready=False,
                restart_count=1,
                waiting_reason="ImagePullBackOff",
                waiting_message="Test message",
            ),
        ],
    )

    findings = imagepull_rule.evaluate(incident)

    assert len(findings) == 1
    assert findings[0].rule == "image_pull"
    assert findings[0].severity == "CRITICAL"
    assert findings[0].title == "Container image cannot be pulled"
    assert findings[0].description == "The container image cannot be downloaded."
    assert findings[0].resource == ResourceRef(
        api_version="v1",
        kind="Pod",
        namespace="test",
        name="test",
    )
    assert findings[0].structured_evidences[0].name == "waiting_reason"
    assert findings[0].structured_evidences[0].value == "ImagePullBackOff"
    assert findings[0].structured_evidences[1].name == "waiting_message"
    assert findings[0].structured_evidences[1].value == "Test message"
    assert findings[0].recommendations == [
        "Verify that the image exists.",
        "Verify the image tag.",
        "Verify the imagePullSecrets.",
        "Verify registry connectivity and authentication.",
    ]
    assert findings[0].metadata == {
        "container": "test",
        "reason": "ImagePullBackOff",
    }


def test_imagepull_rule_with_waiting_reason_errorimagepull(
    imagepull_rule: ImagePullRule,
) -> None:
    incident = Incident(
        namespace="test",
        pod="test",
        phase="Pending",
        observed_at=datetime.now(),
        containers=[
            ContainerSnapshot(
                name="test",
                image="test",
                ready=False,
                restart_count=1,
                waiting_reason="ErrImagePull",
                waiting_message="Test message",
            ),
        ],
    )

    findings = imagepull_rule.evaluate(incident)

    assert len(findings) == 1
    assert findings[0].rule == "image_pull"
    assert findings[0].severity == "CRITICAL"
    assert findings[0].title == "Container image cannot be pulled"
    assert findings[0].description == "The container image cannot be downloaded."
    assert findings[0].resource == ResourceRef(
        api_version="v1",
        kind="Pod",
        namespace="test",
        name="test",
    )
    assert findings[0].structured_evidences[0].name == "waiting_reason"
    assert findings[0].structured_evidences[0].value == "ErrImagePull"
    assert findings[0].structured_evidences[1].name == "waiting_message"
    assert findings[0].structured_evidences[1].value == "Test message"
    assert findings[0].recommendations == [
        "Verify that the image exists.",
        "Verify the image tag.",
        "Verify the imagePullSecrets.",
        "Verify registry connectivity and authentication.",
    ]
    assert findings[0].metadata == {
        "container": "test",
        "reason": "ErrImagePull",
    }


def test_imagepull_rule_without_waiting_reason(
    imagepull_rule: ImagePullRule,
) -> None:
    incident = Incident(
        namespace="test",
        pod="test",
        phase="Running",
        observed_at=datetime.now(),
        containers=[
            ContainerSnapshot(
                name="test",
                image="test",
                ready=True,
                restart_count=0,
            ),
        ],
    )

    findings = imagepull_rule.evaluate(incident)

    assert len(findings) == 0


def test_imagepull_rule_with_multiple_containers(
    imagepull_rule: ImagePullRule,
) -> None:
    incident = Incident(
        namespace="test",
        pod="test",
        phase="Pending",
        observed_at=datetime.now(),
        containers=[
            ContainerSnapshot(
                name="test1",
                image="test1",
                ready=False,
                restart_count=1,
                waiting_reason="ImagePullBackOff",
                waiting_message="Test message",
            ),
            ContainerSnapshot(
                name="test2",
                image="test2",
                ready=False,
                restart_count=1,
                waiting_reason="ErrImagePull",
                waiting_message="Test message",
            ),
        ],
    )

    findings = imagepull_rule.evaluate(incident)

    assert len(findings) == 2
    assert findings[0].structured_evidences[0].name == "waiting_reason"
    assert findings[0].structured_evidences[0].value == "ImagePullBackOff"
    assert findings[0].structured_evidences[1].name == "waiting_message"
    assert findings[0].structured_evidences[1].value == "Test message"
    assert findings[1].structured_evidences[0].name == "waiting_reason"
    assert findings[1].structured_evidences[0].value == "ErrImagePull"
