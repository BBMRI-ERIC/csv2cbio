from ._utilities import write_meta_file, get_template_file_by_name, CbioCSVWriter


def process(options, data):
    # First create resource definition
    write_meta_file(get_template_file_by_name("resource.txt"), f"{options['target_folder']}/meta_resource_definition.txt",
                    options, ["study_id"])

    # First create all resource definitions
    with open(f"{options['target_folder']}/data_resource_definition.txt", 'w') as output:
        # prepare data for resource definition
        res_data = [["RESOURCE_ID", "DISPLAY_NAME", "RESOURCE_TYPE", "DESCRIPTION", "OPEN_BY_DEFAULT", "PRIORITY"]]
        for item in data:
            res = item["resource"]
            res_data.append([
                res["id"].upper(), res["name"], res["resource_type"], res.get("description", "No description provided."), 
                res.get("open_by_default", False), res.get("priority", 1)
            ])

        writer = (
            CbioCSVWriter()
            .with_required_columns("RESOURCE_ID", "DISPLAY_NAME", "RESOURCE_TYPE")
            .with_allowed_values_set("RESOURCE_TYPE", ["SAMPLE", "PATIENT", "STUDY"])
            .with_input(res_data, options=options)
        )
        # Columns for resource definition are built-in defined
        writer.prepare_headers({
            "columns": [{
                "id": "RESOURCE_ID", 
                "name": "ID",
                "description": "Resource ID",
                "data_type": "STRING"
            }, {
                "id": "DISPLAY_NAME",
                "name": "Name",
                "description": "Resource Name",
                "data_type": "STRING"
            }, {
                "id": "RESOURCE_TYPE",
                "name": "Type",
                "description": "Resource type",
                "data_type": "STRING"
            }, {
                "id": "DESCRIPTION",
                "name": "Description",
                "description": "Resource description",
                "data_type": "STRING"
            }, {
                "id": "OPEN_BY_DEFAULT",
                "name": "Default Resource",
                "description": "Open Resource By Default",
                "data_type": "BOOLEAN"
            }, {
                "id": "PRIORITY",
                "name": "Priority",
                "description": "Priority in resources.",
                "data_type": "NUMBER"
            }]
        })
        writer.write_header(output)
        writer.write_data(output)

    for item in data:
        res = item["resource"]
        key = res["__key"]
        rtype = res["resource_type"]
        # First create resource item definition
        write_meta_file(get_template_file_by_name("resource_item.txt"), f"{options['target_folder']}/meta_resource_item_{key}.txt",
                {"study_id": options["study_id"], "filename": f"data_resource_item_{key}.txt", "type": res["resource_type"]})
        
        required_columns = {
            "SAMPLE": ["PATIENT_ID", "SAMPLE_ID", "RESOURCE_ID", "URL"],
            "PATIENT": ["PATIENT_ID", "RESOURCE_ID", "URL"],
            "STUDY": ["RESOURCE_ID", "URL"]
        }
        
        # Then provide all resource items
        with open(f"{options['target_folder']}/data_resource_item_{key}.txt", 'w') as output:
            writer = (
                CbioCSVWriter()
                .with_required_columns(*required_columns[rtype])
                .with_input(item["file"], options)
            )
            writer.prepare_headers(item)
            writer.write_header(output)
            writer.write_data(output)

