import csv
import functools
import gc
import tracemalloc

from pyspark.sql import SparkSession


def monitor_memory(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        is_already_tracing = tracemalloc.is_tracing()
        if not is_already_tracing:
            tracemalloc.start()
        try:
            return func(*args, **kwargs)
        finally:
            if not is_already_tracing:
                current, peak = tracemalloc.get_traced_memory()
                tracemalloc.stop()

                ram_report_writer(
                    {
                        "function": func.__name__,
                        "peak": peak / 1024 / 1024,
                        "current": current / 1024 / 1024,
                    }
                )
                print(
                    f"[RAM REPORT]'{func.__name__}' -> Peak: {peak / 1024 / 1024:.2f} MB, Current: {current / 1024 / 1024:.2f} MB"
                )

            for arg in list(args) + list(kwargs.values()):
                if isinstance(arg, SparkSession):
                    try:
                        arg.catalog.clearCache()
                    except Exception as spark_err:
                        print(f"[Warning] Failed to clear Spark cache: {spark_err}")
                    break

            gc.collect()

    return wrapper


def ram_report_writer(report_data):
    with open("ram_report.csv", "a", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=report_data.keys())
        if file.tell() == 0:
            writer.writeheader()
        writer.writerow(report_data)
