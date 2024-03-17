import os
import numpy as np
import math
import sys
import wfdb
import csv

def NLM_1dDarbon(signal,Nvar,P,PatchHW):
    if isinstance(P,int): # scalar has been entered; expand into patch sample index vector
        P = P-1 #Python start index from 0
        Pvec = np.array(range(-P,P+1))
    else:
        Pvec = P # use the vector that has been input
    signal = np.array(signal)
    #debug = [];
    N = len(signal)

    denoisedSig = np.empty(len(signal)) #NaN * ones(size(signal));
    denoisedSig[:] = np.nan
    # to simpify, don't bother denoising edges
    iStart = PatchHW+1
    iEnd = N - PatchHW
    denoisedSig[iStart: iEnd] = 0

    #debug.iStart = iStart;
    #debug.iEnd = iEnd;

    # initialize weight normalization
    Z = np.zeros(len(signal))
    cnt = np.zeros(len(signal))

    # convert lambda value to  'h', denominator, as in original Buades papers
    Npatch = 2 * PatchHW + 1
    h = 2 * Npatch * Nvar**2

    for idx in Pvec: # loop over all possible differences: s - t
        # do summation over p - Eq.3 in Darbon
        k = np.array(range(N))
        kplus = k + idx
        igood = np.where((kplus >=0) & (kplus < N)) # ignore OOB data; we could also handle it
        SSD = np.zeros(len(k))
        SSD[igood] = (signal[k[igood]] - signal[kplus[igood]])**2
        Sdx = np.cumsum(SSD)

        for ii in range(iStart,iEnd): # loop over all points 's'
            distance = Sdx[ii + PatchHW] - Sdx[ii - PatchHW-1] #Eq 4;this is in place of point - by - point MSE
            # but note the - 1; we want to icnlude the point ii - iPatchHW

            w = math.exp(-distance/h) # Eq 2 in Darbon
            t = ii + idx # in the papers, this is not made explicit

            if t>0 and t<N:
                denoisedSig[ii] = denoisedSig[ii] + w * signal[t]
                Z[ii] = Z[ii] + w
                cnt[ii] = cnt[ii] + 1
                print('ii',ii)
                print('t',t)
                print('w',w)
                print('denoisedSig[ii]', denoisedSig[ii])
                print('Z[ii]',Z[ii])
     # loop over shifts

    # now apply normalization
    denoisedSig = denoisedSig/(Z + sys.float_info.epsilon)
    denoisedSig[0: PatchHW+1] =signal[0: PatchHW+1]
    denoisedSig[ - PatchHW: ] =signal[- PatchHW: ]
    #debug.Z = Z;

def process_file(mat_file_path, hea_file_path, result_folder, file_name):
    # Read the WFDB file using rdsamp function
    signals, metadata = wfdb.rdsamp(hea_file_path)

    # Access metadata information
    fs = metadata['fs']
    sig_len = metadata['sig_len']
    n_sig = metadata['n_sig']
    sig_names = metadata['sig_name']
    units = metadata['units']
    comments = metadata['comments']

    # Apply denoising to each signal
    denoised_signals = []
    for signal_idx in range(n_sig):
        signal = signals[:, signal_idx]

        # Apply NLM denoising
        Nvar = np.std(signal)
        P = 3  # Example value for the patch size
        PatchHW = 1  # Example value for half patch size
        denoised_signal = NLM_1dDarbon(signal, Nvar, P, PatchHW)

        denoised_signals.append(denoised_signal)

    # Prepare CSV file name
    csv_file_name = os.path.join(result_folder, f"{file_name}_denoised.csv")

    # Write denoised signals to CSV file
    with open(csv_file_name, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)

        # Write the header row to the CSV file
        header = ['time'] + sig_names
        writer.writerow(header)

        # Write the denoised signals to the CSV file
        for i in range(sig_len):
            time_stamp = i / fs  # Calculate the time stamp
            row = [time_stamp] + [denoised_signals[j][i] for j in range(n_sig)]
            writer.writerow(row)

    print(f"File {file_name} processed successfully.")


# Main script remains mostly the same
def process_directory(directory, base_dir, result_base_dir):
    result_dir = os.path.join(result_base_dir, directory)
    os.makedirs(result_dir, exist_ok=True)

    # Check if the directory contains a RECORDS file
    records_filename = 'RECORDS'
    records_dir = os.path.join(base_dir, directory.replace('/', os.sep))  # Normalize path separator
    records_file_path = os.path.join(records_dir, records_filename+'.txt')

    if os.path.exists(records_file_path):
        # Read the list of file names from the RECORDS file
        with open(records_file_path, 'r') as records_file:
            for line in records_file:
                file_name = line.strip()
                mat_file_path = os.path.join(base_dir, directory, file_name + '.mat').replace('/', os.sep)
                hea_file_path = os.path.join(base_dir, directory, file_name).replace('/', os.sep)

                # Check if both .mat and .hea files exist
                if os.path.exists(mat_file_path):
                    #Process the file
                    process_file(mat_file_path, hea_file_path, result_dir,file_name)

    # Recursively process subdirectories
    for subdir in os.listdir(records_dir):
        subdir_path = os.path.join(records_dir, subdir)
        if os.path.isdir(subdir_path):
            process_directory(subdir, base_dir, result_base_dir)


# Directory containing the first RECORDS file (which contains paths to subfolders)
records_directory = 'data'
first_records_filename = 'RECORDS.txt'

# Directory to store processed results
result_directory = 'results_denoised'

# Read the list of subfolder paths from the first RECORDS file
with open(os.path.join(records_directory, first_records_filename), 'r') as first_records_file:
    subfolder_paths = first_records_file.read().splitlines()

# Iterate over each subfolder path from the first RECORDS file
for subfolder_path in subfolder_paths:
    process_directory(subfolder_path, records_directory, result_directory)