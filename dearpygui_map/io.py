"""Tile downloading"""

import logging
import queue
import shutil
import tempfile
import threading
from typing import Callable, Iterable
import urllib.request

from dearpygui_map.tile_source import TileSpec


class TileHandler(threading.Thread):

    """Download manager"""

    def __init__(
        self, tile_specs: Iterable[TileSpec], callback: Callable, thread_count: int = 1
    ) -> None:
        threading.Thread.__init__(self)
        self.task_queue = queue.LifoQueue()
        self.result_queue = queue.Queue()
        self.thread_count = thread_count
        self.threads: list[DownloadThread] = []
        self.callback = callback

        for tile_spec in tile_specs:
            self.task_queue.put(tile_spec)

    def run(self):
        """Run download"""
        # TODO add caching
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
                logging.exception(exc)
            finally:
                self.result_queue.task_done()


class DownloadThread(threading.Thread):

    """Threaded downloader"""

    def __init__(self, task_queue: queue.Queue, result_queue: queue.Queue):
        threading.Thread.__init__(self)
        self.task_queue = task_queue
        self.result_queue = result_queue

        # TODO fix proper user agent
        self.user_agent = "Mozilla/5.0 (Windows NT 6.1; Win64; x64)"

    def run(self):
        """Run download"""
        # TODO find out a way to handle failures better
        while not self.task_queue.empty():
            tile_spec: TileSpec = self.task_queue.get()
            req = urllib.request.Request(
                tile_spec.download_url, headers={"User-Agent": self.user_agent}
            )
            try:
                with urllib.request.urlopen(
                    req
                ) as response, tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                    # TODO add error handling etc.
                    shutil.copyfileobj(response, tmp_file)
                tile_spec.download_path = tmp_file.name
                self.result_queue.put(tile_spec)
            except urllib.error.HTTPError as exc:
                logging.exception(exc)

            self.task_queue.task_done()
            # TODO need to store coordinates alongside with image
