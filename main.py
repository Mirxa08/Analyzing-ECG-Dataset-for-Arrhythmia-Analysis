
import os
import wfdb
import csv


tracker = 0
# Open the RECORDS.txt file and read addresses
with open('RECORDS.txt', 'r') as f:
    addresses = [line.strip() for line in f]

    file_index = 1
# Loop through each address line
for address in addresses:
    # Extract the first part of the address (assuming it's the base name)
    base_name = address.split()[0]

    print("NOW FILE IS : ", base_name)
    # Initialize file index

    # Loop to generate file names with incrementing indices
    while True:

        folder_path = base_name
        file_count = len([name for name in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, name))])

        file_count=file_count-1
        file_count=file_count/2
        print(file_count, "--", tracker)

        if tracker == file_count:
            tracker = 0
            break

        # Format the file name with padded zeros
        file_name = os.path.join(base_name, f"JS{file_index:05d}")

        #print("hi 01")
        # Check if file exists before processing
        if os.path.exists(file_name + ".hea"):
            try:

                #print("hi 02")
                # Read the WFDB file using `rdsamp` function
                signals, metadata = wfdb.rdsamp(file_name)

                # Access metadata information
                fs = metadata['fs']
                sig_len = metadata['sig_len']
                n_sig = metadata['n_sig']
                sig_names = metadata['sig_name']
                units = metadata['units']
                comments = metadata['comments']

                # Open a new CSV file for writing

                csv_file_name = os.path.join("CSV", f"JS{file_index:05d}.csv")
                with open(csv_file_name, 'w', newline='') as csvfile:
                    writer = csv.writer(csvfile)

                    # Write the header row to the CSV file
                    header = ['time'] + sig_names
                    writer.writerow(header)

                    # Write the data to the CSV file
                    for i in range(sig_len):
                        time_stamp = i / fs  # Calculate the time stamp
                        row = [time_stamp] + [signals[i][j] for j in range(n_sig)]
                        writer.writerow(row)

                print(f"File {file_name} processed successfully.")
                tracker = tracker + 1

            except Exception as e:
                print(f"Error processing file {file_name}: {str(e)}")
                os.system('PAUSE')
                tracker = tracker + 1

            # Increment the file index
            file_index += 1

        else:
            # Handle the case where the file doesn't exist (optional)
            print(f"File not found: {file_name}")
            file_index += 1

            # Move to the next address if file not found