## Example: CBIO Study from sample list

In this scenario, we generate samples, patients and resources (with verification that resource files do exist),
provide anonymization for patient and sample IDs. All data is stored in a single 'samples' csv with appropriate headers.

````yaml
patients:
  file: "samples.csv"

  # filter patients to have unique values, patients have unique biopsy number
  filter:
    - source_id: Biopsy Number  # original column name in "samples.csv"
      function:
        name: is_unique  # csv2cbio built-in function
        # if we want to use unique check in different part, we just change the key :)
        context: "filter_patients"

  columns:
    # anonymize patient IDs
    # NOTE: such IDs are not fully anonymous if the order of patients is not randomized,
    # since default implementation of ID provider just incrementally provides new IDs.
    # to modify this, you can set    generator: uuid.uuid4
    - id: PATIENT_ID
      source_id: Biopsy Number
      function:
        name: gen_simple_patient_id  # csv2cbio built-in function
        # store biopsy -> ID mapping in this file, optionally override the default filename
        mapper_filename: anonym_patients.csv
        # generator: uuid.uuid4  # safer variant
      name: Patient ID
      description: Unique identifier for the patient
      data_type: STRING

    - id: PT
      source_id: pT
      name: TNM Primary Tumor (pT)
      description: TNM Staging System extent of the tumor
      data_type: STRING

    - id: PN
      source_id: pN
      name: TNM Regional Lymph Nodes (pN)
      description: TNM Staging System extent of spread to the lymph nodes
      data_type: STRING


samples:
  file: "samples.csv"
  columns:
    - id: PATIENT_ID
      source_ids: Biopsy Number
      function:
        name: ret_simple_patient_id  # csv2cbio built-in function, retrieve the value
      name: Patient ID
      description: Unique identifier for the patient
      data_type: STRING

    - id: SAMPLE_ID
      source_ids: ["Year", "Biopsy Number", "Block Number"]
      function:
        # Here, we use fustom-provided function from our functions.py file that takes pd.Series values in
        # internally, the function just calls anonymize(values.aslist().join(delimiter)), anonymize is a built-in function
        # that implements also 'gen_simple_patient_id' logics
        name: my_generate_sample_id
      name: Sample ID
      description: Sample ID
      data_type: STRING


slide_resources:
  file: "samples.csv"

  filter:
    - source_ids: ["Year", "Biopsy Number", "Block Number"]
      function:
        # custom function that takes these values and check such slide exists on the filesystem
        name: my_check_slide_exists

  # define resource
  resource:
    id: SLIDE_WSIS  
    name: WSI Slides
    description: High resolution slides viewed through xOpat
    resource_type: SAMPLE
    open_by_default: false

  # to optimize, create columns that cache the retrieved values
  create:
    - new_column: sample_id_generated
      source_ids: ["Year", "Biopsy Number", "Block Number"]
      function:
        name: my_retrieve_sample_id
    - new_column: patient_id_generated
      source_id: Biopsy Number
      function:
        name: ret_simple_patient_id   # csv2cbio built-in function
  columns:
    - id: RESOURCE_ID
      name: Resource identification
      value: SLIDE_WSIS
    - id: PATIENT_ID
      source_id: patient_id_generated   # newly created column name from above, thus also valid
      name: Patient ID
      description: Unique identifier for the patient
      data_type: STRING
    - id: SAMPLE_ID
      source_id: sample_id_generated
      name: Sample ID
      description: Sample ID
      data_type: STRING
    - id: URL
      # use the generated IDs second time to build slide URL from newly generated, anonymous IDs
      source_ids: [sample_id_generated, patient_id_generated]
      data_type: STRING
      function:
        name: template_string_list   # csv2cbio built-in function
        string: "{server}?slide_list={value[0]}-slide-{value[1]}" 
        template_dict:
          server: https://example.com/xopat/
````