import logging
from pathlib import Path

import gpxpy
import gpxpy.gpx

from config import BASE_PATH

logger = logging.getLogger(__name__)


class GPXStorage:
    """Управление загрузкой/сохранением GPX-файлов с обработкой ошибок."""

    def __init__(self, base_path: Path = BASE_PATH) -> None:
        self.storage_dir = base_path / "gpx_files"
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        self.storage_raw_dir = self.storage_dir / "raw"
        self.storage_raw_dir.mkdir(parents=True, exist_ok=True)

        logger.info("Storage directory set to: %s", self.storage_dir.resolve())

    def find_gpx_files(self, search_path: Path | None = None) -> list[Path]:
        """Рекурсивный поиск GPX-файлов с обработкой ошибок."""
        try:
            if search_path is None:
                search_path = self.storage_raw_dir

            path = Path(search_path).resolve()
            if not path.exists():
                raise FileNotFoundError

            gpx_files = list(path.rglob("*.gpx")) + list(path.rglob("*.GPX"))
            logger.info("Found %d GPX files in %s", len(gpx_files), path)
            return gpx_files
        except FileNotFoundError:
            logger.exception("Directory not found: %s", search_path)
            return []
        except Exception:
            logger.exception("Error finding GPX files")
            return []

    def load_gpx(self, file_path: Path) -> gpxpy.gpx.GPX | None:
        """Загрузка GPX-файла с обработкой ошибок парсинга."""
        try:
            path = Path(file_path)
            with path.open("r", encoding="utf-8") as f:
                content = f.read()
                gpx = gpxpy.parse(content)
                logger.debug("Successfully loaded GPX: %s", path.name)
                return gpx
        except (gpxpy.gpx.GPXException) as e:
            logger.warning("XML parsing error in %s: %s", path.name, e)
        except UnicodeDecodeError:
            logger.warning("Encoding error in %s, trying fallback encoding", path.name)
            try:
                with path.open("r", encoding="latin-1") as f:
                    content = f.read()
                    gpx = gpxpy.parse(content)
                    logger.debug("Successfully loaded with fallback encoding: %s", path.name)
                    return gpx
            except Exception:
                logger.exception("Fallback encoding failed for %s", path.name)
        except Exception:
            logger.exception("Error loading GPX file %s", path.name)
        return None

    def save_gpx(self, gpx: gpxpy.gpx.GPX, filename: str) -> Path | None:
        """Сохранение объекта GPX в файл с обработкой ошибок."""
        try:
            save_path = self.storage_dir / filename
            with save_path.open("w", encoding="utf-8") as f:
                f.write(gpx.to_xml(prettyprint=True))
            logger.info("Saved GPX to: %s", save_path)
            return save_path
        except Exception:
            logger.exception("Error saving GPX file %s", filename)
        return None
