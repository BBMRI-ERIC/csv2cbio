from ._utilities import write_meta_file, get_template_file_by_name, read_opt, pick_color, CbioCSVWriter


def process(options, data):
    write_meta_file(get_template_file_by_name("cancer_type.txt"), f"{options['target_folder']}/meta_cancer_type.txt", {})

    # First create all resource definitions
    with open(f"{options['target_folder']}/data_cancer_type.txt", 'w') as output:
        # prepare data for resource definition, note that the headers ARE NOT written into the output
        res_data = [["TYPE", "NAME", "COLOR", "PARENT"]]
        for cancer_id in data:
            if cancer_id == "tissue":
                raise ValueError("Invalid cancer_type tissue! Reserved word.")

            cancer_data = data[cancer_id]

            res_data.append([
                cancer_id,
                read_opt("name", cancer_data, assert_type=str),
                pick_color(read_opt("ui_color", cancer_data, require=False)),
                read_opt("parent", cancer_data, assert_type=str, require=False, default="tissue"),  # root parent=tissue
            ])

        writer = (
            CbioCSVWriter()
            .with_input(res_data, options=options)
        )
        # Columns for resrouce definition are built-in defined
        writer.prepare_headers({
            "columns": [{
                "id": "TYPE",
                "data_type": "STRING"
            }, {
                "id": "NAME",
                "data_type": "STRING"
            }, {
                "id": "COLOR",
                "data_type": "STRING"
            }, {
                "id": "PARENT",
                "data_type": "STRING"
            }]
        })
        # Headers not expected: writer.write_header(output)
        writer.write_data(output)
