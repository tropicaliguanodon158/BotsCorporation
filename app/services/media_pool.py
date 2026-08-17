from __future__ import annotations

from collections import defaultdict
from threading import Lock

from app.config.media import INTERACTION_IMAGES


class InteractionMediaPool:
    """
    Циклический пул изображений.

    Для каждого interaction command:
    
        image #1
        image #2
        image #3
        image #1
        image #2
        ...

    Никакого random.choice().
    """

    def __init__(self) -> None:
        self._indexes: dict[str, int] = defaultdict(int)
        self._lock = Lock()

    def next(self, interaction: str) -> str | None:
        images = [
            image
            for image in INTERACTION_IMAGES.get(
                interaction,
                [],
            )
            if image
        ]

        if not images:
            return None

        with self._lock:
            index = self._indexes[interaction] % len(images)

            image = images[index]

            self._indexes[interaction] = (
                index + 1
            )

        return image


media_pool = InteractionMediaPool()


def get_command_image(
    command: str,
) -> str | None:
    from app.config.media import COMMAND_IMAGES

    image = COMMAND_IMAGES.get(command)

    if not image:
        return None

    return image