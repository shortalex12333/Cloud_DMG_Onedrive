"""
Metadata extraction from OneDrive file paths.
Maps OneDrive directory structure to doc_type and system_tag.
Ported from PYTHON_LOCAL_CLOUD_PMS/celesteos_agent/metadata_extractor.py
"""

from typing import Dict, List, Optional


# System tag mapping from directory names
SYSTEM_TAG_MAPPING = {
    'Electrical': 'electrical',
    'HVAC': 'hvac',
    'Plumbing': 'plumbing',
    'Engines': 'propulsion',
    'Generators': 'power',
    'Generator': 'power',
    'Navigation': 'navigation',
    'Communications': 'communications',
    'Comms': 'communications',
    'Fire': 'safety',
    'Safety': 'safety',
    'Galley': 'galley',
    'Kitchen': 'galley',
    'Sanitation': 'sanitation',
    'Water': 'water',
    'Fuel': 'fuel',
    'Hydraulic': 'hydraulic',
    'Hydraulics': 'hydraulic',
    'Deck': 'deck',
    'Hull': 'hull',
    'Interior': 'interior',
    'AV': 'av',
    'Audio': 'av',
    'Video': 'av',
    'Entertainment': 'entertainment',
    'CCTV': 'security',
    'Security': 'security',
    'Stabilizers': 'stabilization',
    'Thrusters': 'propulsion',
    'Tender': 'tender',
    'Tenders': 'tender',
}

# Doc type mapping from top-level directory
DOC_TYPE_MAPPING = {
    '01_General': 'general',
    '02_Engineering': 'schematic',
    '03_Systems': 'schematic',
    '04_Manuals': 'manual',
    '05_Drawings': 'drawing',
    '06_Procedures': 'sop',
    '07_Safety': 'sop',
    '08_Maintenance': 'maintenance_log',
    '09_Logs': 'log',
    '10_Inspections': 'inspection',
    '11_Vendors': 'vendor_doc',
    '12_Warranties': 'warranty',
    '13_Certifications': 'certification',
    '14_Photos': 'photo',
    '15_Videos': 'video',
}

# Alternative naming patterns
ALT_DOC_TYPE_MAPPING = {
    'engineering': 'schematic',
    'manuals': 'manual',
    'procedures': 'sop',
    'safety': 'sop',
    'maintenance': 'maintenance_log',
    'logs': 'log',
    'inspections': 'inspection',
    'inspection': 'inspection',
    'vendors': 'vendor_doc',
    'warranties': 'warranty',
    'warranty': 'warranty',
    'certifications': 'certification',
    'certs': 'certification',
    'photos': 'photo',
    'videos': 'video',
    'drawings': 'drawing',
    'schematics': 'schematic',
}


def extract_metadata_from_onedrive_path(onedrive_path: str) -> Dict[str, any]:
    """
    Extract metadata from OneDrive file path.

    Args:
        onedrive_path: OneDrive file path (e.g., "/Engineering/Electrical/main_panel.pdf")

    Returns:
        {
            'system_path': 'Engineering/Electrical',
            'directories': ['Engineering', 'Electrical'],
            'doc_type': 'schematic',
            'system_tag': 'electrical',
            'filename': 'main_panel.pdf'
        }

    Example:
        Input: "/02_Engineering/Electrical/Schematics/main_panel.pdf"
        Output: {
            'system_path': '02_Engineering/Electrical/Schematics',
            'directories': ['02_Engineering', 'Electrical', 'Schematics'],
            'doc_type': 'schematic',
            'system_tag': 'electrical',
            'filename': 'main_panel.pdf'
        }
    """
    # Normalize path (remove leading/trailing slashes)
    path = onedrive_path.strip('/')

    if not path:
        # Empty path
        return {
            'system_path': '',
            'directories': [],
            'doc_type': 'general',
            'system_tag': 'general',
            'filename': ''
        }

    # Split path into parts
    parts = path.split('/')

    # Last part is filename
    filename = parts[-1] if parts else ''

    # Directory parts (exclude filename)
    dir_parts = parts[:-1] if len(parts) > 1 else []

    if not dir_parts:
        # File at root
        return {
            'system_path': '',
            'directories': [],
            'doc_type': 'general',
            'system_tag': 'general',
            'filename': filename
        }

    # System path (directory only, no filename)
    system_path = '/'.join(dir_parts)
    directories = dir_parts

    # Infer doc_type from top-level directory
    top_level = dir_parts[0]
    doc_type = DOC_TYPE_MAPPING.get(top_level)

    # Fallback: check alternative patterns
    if not doc_type:
        top_level_lower = top_level.lower()
        doc_type = ALT_DOC_TYPE_MAPPING.get(top_level_lower, 'general')

    # Infer system_tag from any matching directory
    system_tag = 'general'
    for part in dir_parts:
        if part in SYSTEM_TAG_MAPPING:
            system_tag = SYSTEM_TAG_MAPPING[part]
            break
        # Try case-insensitive match
        for key, value in SYSTEM_TAG_MAPPING.items():
            if key.lower() in part.lower():
                system_tag = value
                break

    return {
        'system_path': system_path,
        'directories': directories,
        'doc_type': doc_type,
        'system_tag': system_tag,
        'filename': filename
    }


def format_for_digest_service(
    onedrive_path: str,
    filename: str,
    yacht_id: str
) -> Dict[str, any]:
    """
    Format metadata for digest service endpoint.

    Args:
        onedrive_path: OneDrive file path
        filename: File name
        yacht_id: Yacht identifier

    Returns:
        Formatted data for POST to celeste-digest-index.onrender.com
    """
    metadata = extract_metadata_from_onedrive_path(onedrive_path)

    return {
        'yacht_id': yacht_id,
        'filename': filename,
        'system_path': metadata['system_path'],
        'directories': metadata['directories'],
        'doc_type': metadata['doc_type'],
        'system_tag': metadata['system_tag'],
        'source': 'onedrive'  # Mark as from OneDrive (vs NAS)
    }
