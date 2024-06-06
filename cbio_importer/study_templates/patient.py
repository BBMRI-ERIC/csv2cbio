from ._utilities import write_meta_file, get_template_file_by_name, CbioCSVWriter


def process(options, data):
    write_meta_file(get_template_file_by_name("patient.txt"), f"{options['target_folder']}/meta_clinical_patient.txt",
                    options, ["study_id"])
    
    # Now parse the data
    with open(f"{options['target_folder']}/data_clinical_patient.txt", 'w') as output:
        writer = (
            CbioCSVWriter()
            .with_required_columns("PATIENT_ID")
            .with_input(data["file"], options)
        )
        writer.prepare_headers(data)

        # First write compulsory headers:
        writer.write_comment_ids(output)
        writer.write_comment_descriptions(output)
        writer.write_comment_data_types(output)
        writer.write_comment_priority(output)
        writer.write_header(output)
        # Then, write the data
        writer.write_data(output)
