#!/usr/bin/env python3
"""
XGMML Rebuilder Script - Fixed Version
Properly combines incomplete XGMML (edges only) with FASTA sequences and metadata
"""

import re
import sys
from pathlib import Path

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
    """Main function to rebuild complete XGMML"""
    print("Parsing input files...")
    
    # Parse all input files
    sequences = parse_fasta(fasta_file)
    descriptions = parse_metadata_tab(metadata_file)
    node_ids, original_content = extract_node_ids_from_xgmml(xgmml_file)
    
    print(f"Found {len(sequences)} sequences")
    print(f"Found {len(descriptions)} descriptions")
    print(f"Found {len(node_ids)} unique node IDs in edges")
    
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
            print(f"Warning: Limited data found for node {node_id}")
    
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
    
    print(f"\nRebuild complete!")
    print(f"- Added {nodes_added} nodes")
    print(f"- {nodes_missing_data} nodes had missing sequence/metadata")
    print(f"- Output written to: {output_file}")

def main():
    """Command line interface"""
    if len(sys.argv) != 5:
        print("Usage: python rebuild_xgmml.py <input.xgmml> <sequences.fasta> <metadata.tab> <output.xgmml>")
        print("\nExample:")
        print("python rebuild_xgmml.py incomplete.xgmml filtered_sequences.fasta filtered_sequence_metadata.tab complete.xgmml")
        sys.exit(1)
    
    xgmml_file = sys.argv[1]
    fasta_file = sys.argv[2]
    metadata_file = sys.argv[3]
    output_file = sys.argv[4]
    
    # Check if input files exist
    for file_path in [xgmml_file, fasta_file, metadata_file]:
        if not Path(file_path).exists():
            print(f"Error: File not found: {file_path}")
            sys.exit(1)
    
    try:
        rebuild_xgmml(xgmml_file, fasta_file, metadata_file, output_file)
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()