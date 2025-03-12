from ._utilities import write_meta_file, get_template_file_by_name, CbioCSVWriter


def process(options, data):

    for item in data:
        series = item["series"]
        key = series["__key"]
        # First create resource item definition
        write_meta_file(get_template_file_by_name("time_series.txt"), f"{options['target_folder']}/meta_timeline_{key}.txt",
            {"study_id": options["study_id"], "filename": f"data_timeline_{key}.txt"})

        # Then provide all resource items
        with open(f"{options['target_folder']}/data_timeline_{key}.txt", 'w') as output:
            writer = (
                CbioCSVWriter()
                .with_required_columns("PATIENT_ID", "START_DATE", "STOP_DATE", "EVENT_TYPE")
                .with_input(item["file"], options)
            )
            writer.prepare_headers(item)
            writer.write_header(output)
            writer.write_data(output)

