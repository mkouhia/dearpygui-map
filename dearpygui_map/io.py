"""Tile downloading"""

import logging
import queue
import shutil
import threading
from typing import Callable, Iterable
import urllib.request

from ._version import __version__
from .tile_source import TileSpec


logger = logging.getLogger(__name__)


class TileHandler(threading.Thread):

    """Caching, threaded download manager"""

    def __init__(
        self, tile_specs: Iterable[TileSpec], callback: Callable, thread_count: int = 1
    ) -> None:
        threading.Thread.__init__(self)
        self.task_queue = queue.LifoQueue()
        self.result_queue = queue.Queue()
        self.thread_count = thread_count
        self.threads: list[DownloadThread] = []
        self.callback = callback

        self.add_to_queue(tile_specs)

    def add_to_queue(self, tile_specs: Iterable[TileSpec]) -> None:
        """Find tiles from cache or add tiles to download queue

        Args:
            tile_specs (Iterable[TileSpec]): tiles to be downloaded
        """
        for tile_spec in tile_specs:
            if tile_spec.local_storage_path.exists():
                self.result_queue.put(tile_spec)
            else:
                self.task_queue.put(tile_spec)

    def run(self):
        """Run download"""
        for _ in range(self.thread_count):
            thread = DownloadThread(self.task_queue, self.result_queue)
            thread.start()
            self.threads.append(thread)
        while not (
            self.result_queue.empty() and sum([t.is_alive() for t in self.threads]) == 0
        ):
            result: TileSpec = self.result_queue.get()
            try:
                self.callback(result)
            except Exception as exc:  # pylint: disable=broad-except
                logger.error(exc)
            finally:
                self.result_queue.task_done()


class DownloadThread(threading.Thread):

    """Threaded downloader"""

    def __init__(self, task_queue: queue.Queue, result_queue: queue.Queue):
        threading.Thread.__init__(self)
        self.task_queue = task_queue
        self.result_queue = result_queue

        self.user_agent = f"dearpygui-map/{__version__}"

    def run(self):
        """Run download"""
        # TODO find out a way to handle failures better
        while not self.task_queue.empty():
            tile_spec: TileSpec = self.task_queue.get()
            req = urllib.request.Request(
                tile_spec.download_url, headers={"User-Agent": self.user_agent}
            )
            try:
                tile_path = tile_spec.local_storage_path
                tile_path.parent.mkdir(parents=True, exist_ok=True)
                with urllib.request.urlopen(req) as response, open(
                    tile_path, "wb"
                ) as local_file:
                    # TODO add error handling etc.
                    shutil.copyfileobj(response, local_file)
                self.result_queue.put(tile_spec)
            except urllib.error.HTTPError as exc:
                logger.error(
                    "%s, url: %s", exc, tile_spec.download_url, exc_info=False
                )

            self.task_queue.task_done()
            # TODO need to store coordinates alongside with image
