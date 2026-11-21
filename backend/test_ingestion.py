from ingestion import CameraTrapProcessor


INPUT_FOLDER = r"E:\tiger dataset\archive\tigers\test"


processor = CameraTrapProcessor()

report = processor.process_folder(
    INPUT_FOLDER
)

print("\n==============================")
print("       PENCHAI REPORT")
print("==============================")

print(
    f"Processed: {report['processed']}"
)

print(
    f"Subjects: {report['subjects']}"
)

print(
    f"Blank: {report['blank']}"
)

print(
    f"Tigers: {report['tigers']}"
)

print(
    f"Errors: {report['errors']}"
)

print(
    f"Time: {report['elapsed_seconds']} seconds"
)

print(
    f"Speed: {report['images_per_second']} images/sec"
)

print(
    "\nResults saved inside:"
)

print(
    INPUT_FOLDER + r"\_penchai"
)   