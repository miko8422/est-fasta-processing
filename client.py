# #!/usr/bin/env python3
# """
# FASTA Processing API Client
# Sends FASTA file and parameters to the API server
# """

# import requests
# import sys
# import argparse
# import os
# import zipfile
# import tempfile

# def process_fasta_file(server_url, fasta_file_path, filter_min_val=23, output_dir=None):
#     """
#     Send FASTA file to API server for processing
    
#     Args:
#         server_url: URL of the API server (e.g., http://localhost:5000)
#         fasta_file_path: Path to the FASTA file to process
#         filter_min_val: Minimum filter value for SSN generation (default: 23)
#         output_dir: Directory where to save the output files (optional)
    
#     Returns:
#         True if successful, False otherwise
#     """
#     # Prepare the endpoint URL
#     endpoint = f"{server_url}/process"
    
#     # Check if file exists
#     if not os.path.exists(fasta_file_path):
#         print(f"Error: File not found: {fasta_file_path}")
#         return False
    
#     # Set up output directory
#     if output_dir is None:
#         output_dir = "output"
    
#     # Create output directory if it doesn't exist
#     os.makedirs(output_dir, exist_ok=True)
    
#     try:
#         # Prepare the files and data
#         with open(fasta_file_path, 'rb') as f:
#             files = {'file': (os.path.basename(fasta_file_path), f, 'application/octet-stream')}
#             data = {'filter_min_val': str(filter_min_val)}
            
#             print(f"Uploading {fasta_file_path} to {endpoint}...")
#             print(f"Using filter_min_val: {filter_min_val}")
            
#             # Make the request
#             response = requests.post(endpoint, files=files, data=data, timeout=1800)  # 30 min timeout
        
#         # Check response
#         if response.status_code == 200:
#             # Save the zip file temporarily
#             with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as temp_zip:
#                 temp_zip.write(response.content)
#                 temp_zip_path = temp_zip.name
            
#             try:
#                 # Extract the zip file
#                 with zipfile.ZipFile(temp_zip_path, 'r') as zip_ref:
#                     zip_ref.extractall(output_dir)
#                     extracted_files = zip_ref.namelist()
                
#                 print(f"Success! Extracted files to: {output_dir}")
#                 print("Files extracted:")
#                 for file in extracted_files:
#                     file_path = os.path.join(output_dir, file)
#                     if os.path.exists(file_path):
#                         file_size = os.path.getsize(file_path)
#                         print(f"  - {file} ({file_size} bytes)")
#                     else:
#                         print(f"  - {file} (not found)")
                
#                 # Clean up temporary zip file
#                 os.unlink(temp_zip_path)
#                 return True
                
#             except zipfile.BadZipFile:
#                 print("Error: Received invalid zip file from server")
#                 # Clean up temporary zip file
#                 os.unlink(temp_zip_path)
#                 return False
#             except Exception as e:
#                 print(f"Error extracting zip file: {e}")
#                 # Clean up temporary zip file
#                 os.unlink(temp_zip_path)
#                 return False
#         else:
#             print(f"Error: Server returned status code {response.status_code}")
#             try:
#                 error_msg = response.json().get('error', 'Unknown error')
#                 print(f"Error message: {error_msg}")
                
#                 # Show missing files if available
#                 missing_files = response.json().get('missing_files', [])
#                 if missing_files:
#                     print(f"Missing files: {missing_files}")
#             except:
#                 print(f"Response: {response.text}")
#             return False
            
#     except requests.exceptions.ConnectionError:
#         print(f"Error: Could not connect to server at {server_url}")
#         print("Make sure the server is running.")
#         return False
#     except requests.exceptions.Timeout:
#         print("Error: Request timed out. The processing might take longer than expected.")
#         return False
#     except Exception as e:
#         print(f"Error: {str(e)}")
#         return False

# def check_server_health(server_url):
#     """Check if the server is running"""
#     try:
#         response = requests.get(f"{server_url}/health", timeout=5)
#         return response.status_code == 200
#     except:
#         return False

# def main():
#     parser = argparse.ArgumentParser(description='FASTA Processing API Client')
#     parser.add_argument('fasta_file', help='Path to the FASTA file to process')
#     parser.add_argument('--server', default='http://localhost:7860',
#                         help='API server URL (default: http://localhost:7860)')
#     parser.add_argument('--filter-min-val', type=int, default=23,
#                         help='Minimum filter value for SSN generation (default: 23)')
#     parser.add_argument('--output-dir', '-o', default='output',
#                         help='Output directory path (default: output)')
    
#     args = parser.parse_args()
    
#     # Check server health
#     print(f"Checking server at {args.server}...")
#     if not check_server_health(args.server):
#         print("Error: Server is not responding. Make sure the server is running.")
#         sys.exit(1)
    
#     print("Server is healthy!")
    
#     # Process the file
#     success = process_fasta_file(
#         args.server,
#         args.fasta_file,
#         args.filter_min_val,
#         args.output_dir
#     )
    
#     sys.exit(0 if success else 1)

# if __name__ == '__main__':
#     main()

#!/usr/bin/env python3
"""
FASTA Processing API Client with Integrated XGMML Rebuild
Sends FASTA file to API server and automatically rebuilds complete XGMML
"""

import requests
import sys
import argparse
import os
import zipfile
import tempfile
import re

def parse_fasta(fasta_file):
    """Parse FASTA file and return dict of {header_id: sequence}"""
    sequences = {}
    
    with open(fasta_file, 'r') as f:
        content = f.read()
    
    # Split by > and process each entry
    entries = content.split('>')[1:]  # Skip first empty element
    
    for entry in entries:
        lines = entry.strip().split('\n')
        if lines:
            header = lines[0].strip()
            sequence = ''.join(lines[1:]).replace('\n', '').replace(' ', '')
            sequences[header] = sequence
    
    return sequences

def parse_metadata_tab(tab_file):
    """Parse metadata tab file and return dict of {seq_id: description}"""
    descriptions = {}
    
    with open(tab_file, 'r') as f:
        lines = f.readlines()
    
    # Skip header line
    for line in lines[1:]:
        parts = line.strip().split('\t')
        if len(parts) >= 3:
            seq_id = parts[0]
            attribute = parts[1]
            value = parts[2]
            
            # We only care about Description attribute
            if attribute == 'Description':
                descriptions[seq_id] = value
    
    return descriptions

def extract_node_ids_from_xgmml(xgmml_file):
    """Extract all unique node IDs referenced in edges from XGMML text"""
    with open(xgmml_file, 'r') as f:
        content = f.read()
    
    # Find all source and target attributes in edge elements
    node_ids = set()
    
    # Pattern to match source="..." and target="..." in edge elements
    source_pattern = r'<edge[^>]*source="([^"]*)"'
    target_pattern = r'<edge[^>]*target="([^"]*)"'
    
    sources = re.findall(source_pattern, content)
    targets = re.findall(target_pattern, content)
    
    node_ids.update(sources)
    node_ids.update(targets)
    
    return node_ids, content

def create_node_xml(node_id, sequences, descriptions):
    """Create XML string for a single node"""
    # Find matching sequence (case insensitive)
    sequence = ""
    seq_length = 0
    
    for header, seq in sequences.items():
        if header.upper() == node_id.upper():
            sequence = seq
            seq_length = len(seq)
            break
    
    # Find matching description (case insensitive)  
    description = "Unknown"
    for desc_id, desc in descriptions.items():
        if desc_id.upper() == node_id.upper():
            description = desc
            break
    
    # Create the node XML string with exact formatting
    node_xml = f'''  <node id="{node_id}" label="{node_id}">
    <att name="Sequence Source" type="string" value="USER" />
    <att name="Sequence Length" type="integer" value="{seq_length}" />
    <att type="list" name="Other IDs">
      <att type="string" name="Other IDs" value="None" />
    </att>
    <att name="Sequence" type="string" value="{sequence}" />
    <att type="list" name="Description">
      <att type="string" name="Description" value="{description}" />
    </att>
  </node>'''
    
    return node_xml

def rebuild_xgmml(xgmml_file, fasta_file, metadata_file, output_file):
    """Rebuild complete XGMML from incomplete XGMML + FASTA + metadata"""
    print("Rebuilding complete XGMML...")
    
    # Parse all input files
    sequences = parse_fasta(fasta_file)
    descriptions = parse_metadata_tab(metadata_file)
    node_ids, original_content = extract_node_ids_from_xgmml(xgmml_file)
    
    print(f"  - Found {len(sequences)} sequences")
    print(f"  - Found {len(descriptions)} descriptions")
    print(f"  - Found {len(node_ids)} unique node IDs in edges")
    
    # Create all node XML strings
    node_xmls = []
    nodes_added = 0
    nodes_missing_data = 0
    
    for node_id in sorted(node_ids):
        node_xml = create_node_xml(node_id, sequences, descriptions)
        node_xmls.append(node_xml)
        nodes_added += 1
        
        # Check if we found data for this node
        found_seq = any(header.upper() == node_id.upper() for header in sequences.keys())
        found_desc = any(desc_id.upper() == node_id.upper() for desc_id in descriptions.keys())
        
        if not found_seq or not found_desc:
            nodes_missing_data += 1
    
    # Insert nodes into the original XGMML content
    # Find the position after the <graph> opening tag but before the first <edge>
    
    # Find the graph opening tag
    graph_pattern = r'(<graph[^>]*>)'
    graph_match = re.search(graph_pattern, original_content)
    
    if not graph_match:
        raise ValueError("Could not find <graph> opening tag in XGMML file")
    
    # Find the first edge
    first_edge_pattern = r'(<edge[^>]*>)'
    first_edge_match = re.search(first_edge_pattern, original_content)
    
    if not first_edge_match:
        raise ValueError("Could not find any <edge> elements in XGMML file")
    
    # Insert position is right before the first edge
    insert_pos = first_edge_match.start()
    
    # Combine all node XMLs
    all_nodes = '\n'.join(node_xmls) + '\n'
    
    # Insert nodes into the content
    new_content = original_content[:insert_pos] + all_nodes + original_content[insert_pos:]
    
    # Write the complete XGMML
    with open(output_file, 'w') as f:
        f.write(new_content)
    
    print(f"  - Added {nodes_added} nodes")
    if nodes_missing_data > 0:
        print(f"  - Warning: {nodes_missing_data} nodes had missing sequence/metadata")
    print(f"  - Complete XGMML written to: {output_file}")
    
    return True

def process_fasta_file(server_url, fasta_file_path, filter_min_val=23, output_dir=None, keep_intermediate=False):
    """
    Send FASTA file to API server for processing and rebuild complete XGMML
    
    Args:
        server_url: URL of the API server (e.g., http://localhost:5000)
        fasta_file_path: Path to the FASTA file to process
        filter_min_val: Minimum filter value for SSN generation (default: 23)
        output_dir: Directory where to save the output files (optional)
        keep_intermediate: Whether to keep the intermediate files (default: False)
    
    Returns:
        True if successful, False otherwise
    """
    # Prepare the endpoint URL
    endpoint = f"{server_url}/process"
    
    # Check if file exists
    if not os.path.exists(fasta_file_path):
        print(f"Error: File not found: {fasta_file_path}")
        return False
    
    # Set up output directory
    if output_dir is None:
        output_dir = "output"
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        # Prepare the files and data
        with open(fasta_file_path, 'rb') as f:
            files = {'file': (os.path.basename(fasta_file_path), f, 'application/octet-stream')}
            data = {'filter_min_val': str(filter_min_val)}
            
            print(f"Uploading {fasta_file_path} to {endpoint}...")
            print(f"Using filter_min_val: {filter_min_val}")
            
            # Make the request
            response = requests.post(endpoint, files=files, data=data, timeout=1800)  # 30 min timeout
        
        # Check response
        if response.status_code == 200:
            # Save the zip file temporarily
            with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as temp_zip:
                temp_zip.write(response.content)
                temp_zip_path = temp_zip.name
            
            try:
                # Extract the zip file
                with zipfile.ZipFile(temp_zip_path, 'r') as zip_ref:
                    zip_ref.extractall(output_dir)
                    extracted_files = zip_ref.namelist()
                
                print(f"Success! Extracted files to: {output_dir}")
                print("Files extracted:")
                for file in extracted_files:
                    file_path = os.path.join(output_dir, file)
                    if os.path.exists(file_path):
                        file_size = os.path.getsize(file_path)
                        print(f"  - {file} ({file_size} bytes)")
                    else:
                        print(f"  - {file} (not found)")
                
                # Clean up temporary zip file
                os.unlink(temp_zip_path)
                
                # Now rebuild the complete XGMML
                print("\n" + "="*50)
                
                # Define expected file paths
                xgmml_file = os.path.join(output_dir, "ssn.xgmml")
                fasta_file = os.path.join(output_dir, "filtered_sequences.fasta")
                metadata_file = os.path.join(output_dir, "filtered_sequence_metadata.tab")
                complete_xgmml_file = os.path.join(output_dir, "complete_ssn.xgmml")
                
                # Check if all required files exist
                missing_files = []
                for filepath, name in [(xgmml_file, "ssn.xgmml"), 
                                     (fasta_file, "filtered_sequences.fasta"), 
                                     (metadata_file, "filtered_sequence_metadata.tab")]:
                    if not os.path.exists(filepath):
                        missing_files.append(name)
                
                if missing_files:
                    print(f"Error: Missing required files for rebuild: {missing_files}")
                    return False
                
                # Rebuild the complete XGMML
                try:
                    success = rebuild_xgmml(xgmml_file, fasta_file, metadata_file, complete_xgmml_file)
                    
                    if success:
                        print("\n" + "="*50)
                        print("✅ Processing Complete!")
                        print(f"📁 Output directory: {output_dir}")
                        print(f"🎯 Final result: complete_ssn.xgmml")
                        
                        # Show final file size
                        if os.path.exists(complete_xgmml_file):
                            final_size = os.path.getsize(complete_xgmml_file)
                            print(f"📊 Complete XGMML size: {final_size} bytes")
                        
                        # Clean up intermediate files if requested
                        if not keep_intermediate:
                            print("\n🧹 Cleaning up intermediate files...")
                            for filepath in [xgmml_file, fasta_file, metadata_file]:
                                try:
                                    if os.path.exists(filepath):
                                        os.remove(filepath)
                                        print(f"  - Removed {os.path.basename(filepath)}")
                                except Exception as e:
                                    print(f"  - Warning: Could not remove {os.path.basename(filepath)}: {e}")
                        else:
                            print(f"\n📋 Intermediate files kept in: {output_dir}")
                        
                        return True
                    else:
                        print("Error: Failed to rebuild XGMML")
                        return False
                        
                except Exception as e:
                    print(f"Error during XGMML rebuild: {e}")
                    return False
                
            except zipfile.BadZipFile:
                print("Error: Received invalid zip file from server")
                # Clean up temporary zip file
                os.unlink(temp_zip_path)
                return False
            except Exception as e:
                print(f"Error extracting zip file: {e}")
                # Clean up temporary zip file
                os.unlink(temp_zip_path)
                return False
        else:
            print(f"Error: Server returned status code {response.status_code}")
            try:
                error_msg = response.json().get('error', 'Unknown error')
                print(f"Error message: {error_msg}")
                
                # Show missing files if available
                missing_files = response.json().get('missing_files', [])
                if missing_files:
                    print(f"Missing files: {missing_files}")
            except:
                print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"Error: Could not connect to server at {server_url}")
        print("Make sure the server is running.")
        return False
    except requests.exceptions.Timeout:
        print("Error: Request timed out. The processing might take longer than expected.")
        return False
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def check_server_health(server_url):
    """Check if the server is running"""
    try:
        response = requests.get(f"{server_url}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def main():
    parser = argparse.ArgumentParser(description='FASTA Processing API Client with Integrated XGMML Rebuild')
    parser.add_argument('fasta_file', help='Path to the FASTA file to process')
    parser.add_argument('--server', default='http://localhost:7860',
                        help='API server URL (default: http://localhost:7860)')
    parser.add_argument('--filter-min-val', type=int, default=23,
                        help='Minimum filter value for SSN generation (default: 23)')
    parser.add_argument('--output-dir', '-o', default='output',
                        help='Output directory path (default: output)')
    parser.add_argument('--keep-intermediate', action='store_true',
                        help='Keep intermediate files (ssn.xgmml, .fasta, .tab) after rebuild')
    
    args = parser.parse_args()
    
    # Check server health
    print(f"Checking server at {args.server}...")
    if not check_server_health(args.server):
        print("Error: Server is not responding. Make sure the server is running.")
        sys.exit(1)
    
    print("Server is healthy!")
    
    # Process the file
    success = process_fasta_file(
        args.server,
        args.fasta_file,
        args.filter_min_val,
        args.output_dir,
        args.keep_intermediate
    )
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()