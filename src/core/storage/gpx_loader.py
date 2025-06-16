import logging
from pathlib import Path
from typing import Optional, Union

import gpxpy
import gpxpy.gpx

logger = logging.getLogger("GPXStorage")


class GPXStorage:
    """Управление загрузкой/сохранением GPX-файлов с обработкой ошибок"""

    def __init__(self, base_dir: Path = "gpx_storage"):
        self.storage_dir = base_dir / "gpx_files"
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Storage directory set to: {self.storage_dir.resolve()}")

    def find_gpx_files(self, search_path: Union[str, Path]) -> list[Path]:
        """Рекурсивный поиск GPX-файлов с обработкой ошибок"""
        try:
            path = Path(search_path).resolve()
            if not path.exists():
                raise FileNotFoundError(f"Path not found: {path}")

            gpx_files = list(path.rglob("*.gpx")) + list(path.rglob("*.GPX"))
            logger.info(f"Found {len(gpx_files)} GPX files in {path}")
            return gpx_files

        except Exception as e:
            logger.error(f"Error finding GPX files: {e}", exc_info=True)
            return []

    def load_gpx(self, file_path: Union[str, Path]) -> Optional[gpxpy.gpx.GPX]:
        """Загрузка GPX-файла с обработкой ошибок парсинга"""
        try:
            path = Path(file_path)
            with path.open('r', encoding='utf-8') as f:
                content = f.read()
                gpx = gpxpy.parse(content)
                logger.debug(f"Successfully loaded GPX: {path.name}")
                return gpx
        except (gpxpy.gpx.GPXException) as e:
            logger.warning(f"XML parsing error in {path.name}: {e}")
        except UnicodeDecodeError:
            logger.warning(f"Encoding error in {path.name}, trying fallback encoding")
            try:
                with path.open('r', encoding='latin-1') as f:
                    content = f.read()
                    gpx = gpxpy.parse(content)
                    logger.debug(f"Successfully loaded with fallback encoding: {path.name}")
                    return gpx
            except Exception as e:
                logger.error(f"Fallback encoding failed for {path.name}: {e}")
        except Exception as e:
            logger.error(f"Error loading GPX file {path.name}: {e}", exc_info=True)
        return None

    def save_gpx(self, gpx: gpxpy.gpx.GPX, filename: str) -> Optional[Path]:
        """Сохранение объекта GPX в файл с обработкой ошибок"""
        try:
            save_path = self.storage_dir / filename
            with save_path.open('w', encoding='utf-8') as f:
                f.write(gpx.to_xml(prettyprint=True))
            logger.info(f"Saved GPX to: {save_path}")
            return save_path
        except Exception as e:
            logger.error(f"Error saving GPX file {filename}: {e}", exc_info=True)
            return None
