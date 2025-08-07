"""
Mirror management and testing functionality
"""

import asyncio
import time
import urllib.request
import concurrent.futures
from typing import List, Tuple, Optional
from utils.logging import get_logger
from config.settings import MIRROR_TEST_TIMEOUT, MIRROR_TEST_SIZE, MAX_PARALLEL_MIRRORS

logger = get_logger(__name__)

# Comprehensive worldwide mirror list
WORLDWIDE_MIRRORS = [
    # North America
    ('🇺🇸 Rackspace (Texas)', 'https://mirror.rackspace.com/archlinux/$repo/os/$arch'),
    ('🇺🇸 MIT (Massachusetts)', 'https://mirrors.mit.edu/archlinux/$repo/os/$arch'),
    ('🇺🇸 Kernel.org (California)', 'https://mirrors.kernel.org/archlinux/$repo/os/$arch'),
    ('🇺🇸 Georgia Tech', 'https://www.gtlib.gatech.edu/pub/archlinux/$repo/os/$arch'),
    ('🇺🇸 University of Utah', 'https://arch.mirror.constant.com/$repo/os/$arch'),
    ('🇨🇦 University of Waterloo', 'https://mirror.csclub.uwaterloo.ca/archlinux/$repo/os/$arch'),
    ('🇨🇦 Carleton University', 'https://mirror.carleton.ca/archlinux/$repo/os/$arch'),
    
    # Europe
    ('🇩🇪 rwth-aachen.de', 'https://mirror.rwth-aachen.de/archlinux/$repo/os/$arch'),
    ('🇩🇪 FAU Erlangen', 'https://ftp.fau.de/archlinux/$repo/os/$arch'),
    ('🇩🇪 TU Chemnitz', 'https://ftp.tu-chemnitz.de/pub/linux/archlinux/$repo/os/$arch'),
    ('🇫🇷 Ircam', 'https://mirrors.ircam.fr/pub/archlinux/$repo/os/$arch'),
    ('🇫🇷 Telecom ParisTech', 'https://mirror.telepoint.bg/archlinux/$repo/os/$arch'),
    ('🇬🇧 University of Cambridge', 'https://www.mirrorservice.org/sites/ftp.archlinux.org/$repo/os/$arch'),
    ('🇬🇧 Bytemark', 'https://lon.mirror.rackspace.com/archlinux/$repo/os/$arch'),
    ('🇳🇱 Nluug', 'https://ftp.nluug.nl/os/Linux/distr/archlinux/$repo/os/$arch'),
    ('🇳🇱 Leaseweb', 'https://mirror.leaseweb.com/archlinux/$repo/os/$arch'),
    ('🇸🇪 Lysator', 'https://ftp.lysator.liu.se/pub/archlinux/$repo/os/$arch'),
    ('🇳🇴 University of Oslo', 'https://mirrors.dotsrc.org/archlinux/$repo/os/$arch'),
    ('🇨🇭 Switch.ch', 'https://mirror.switch.ch/ftp/mirror/archlinux/$repo/os/$arch'),
    ('🇮🇹 Garr', 'https://archlinux.mirror.garr.it/mirrors/archlinux/$repo/os/$arch'),
    ('🇪🇸 RedIRIS', 'https://ftp.rediris.es/mirror/archlinux/$repo/os/$arch'),
    
    # Asia-Pacific
    ('🇯🇵 JAIST', 'https://ftp.jaist.ac.jp/pub/Linux/ArchLinux/$repo/os/$arch'),
    ('🇯🇵 Tsukuba University', 'https://ftp.tsukuba.wide.ad.jp/Linux/archlinux/$repo/os/$arch'),
    ('🇰🇷 KAIST', 'https://ftp.kaist.ac.kr/ArchLinux/$repo/os/$arch'),
    ('🇨🇳 Tsinghua University', 'https://mirrors.tuna.tsinghua.edu.cn/archlinux/$repo/os/$arch'),
    ('🇨🇳 USTC', 'https://mirrors.ustc.edu.cn/archlinux/$repo/os/$arch'),
    ('🇸🇬 National University', 'https://download.nus.edu.sg/mirror/archlinux/$repo/os/$arch'),
    ('🇦🇺 AARNet', 'https://mirror.aarnet.edu.au/pub/archlinux/$repo/os/$arch'),
    ('🇦🇺 Internode', 'https://mirror.internode.on.net/pub/archlinux/$repo/os/$arch'),
    ('🇮🇳 Indian Institute of Technology', 'https://mirror.cse.iitk.ac.in/archlinux/$repo/os/$arch'),
    
    # South America
    ('🇧🇷 University of São Paulo', 'https://br.mirror.archlinux-br.org/$repo/os/$arch'),
    ('🇧🇷 C3SL UFPR', 'https://archlinux.c3sl.ufpr.br/$repo/os/$arch'),
    ('🇨🇱 University of Chile', 'https://mirror.uchile.cl/archlinux/$repo/os/$arch'),
    
    # Africa
    ('🇿🇦 University of the Witwatersrand', 'https://archlinux.mirror.ac.za/$repo/os/$arch'),
    
    # Global CDNs
    ('🌍 Worldwide CDN', 'https://geo.mirror.pkgbuild.com/$repo/os/$arch'),
    ('🌍 CloudFlare CDN', 'https://cloudflaremirrors.com/archlinux/$repo/os/$arch'),
]

def test_mirror_speed(mirror_data: Tuple[str, str], timeout: int = MIRROR_TEST_TIMEOUT) -> Tuple[str, str, Optional[int], Optional[str]]:
    """
    Test mirror speed by downloading a small file
    Returns: (name, url, speed_ms, error_msg)
    """
    name, url = mirror_data
    
    try:
        # Create test URL
        test_url = url.replace('$repo', 'core').replace('$arch', 'x86_64') + '/core.db'
        
        # Create request with proper headers
        request = urllib.request.Request(
            test_url,
            headers={
                'User-Agent': 'GamerX-Installer/3.0 (Arch Linux)'
            }
        )
        
        # Time the request
        start_time = time.time()
        
        with urllib.request.urlopen(request, timeout=timeout) as response:
            # Read limited amount of data
            data = response.read(MIRROR_TEST_SIZE)
            
        end_time = time.time()
        speed_ms = int((end_time - start_time) * 1000)
        
        logger.debug(f"Mirror {name}: {speed_ms}ms")
        return name, url, speed_ms, None
        
    except Exception as e:
        error_msg = str(e)[:50] + "..." if len(str(e)) > 50 else str(e)
        logger.debug(f"Mirror {name} failed: {error_msg}")
        return name, url, None, error_msg

async def test_mirrors_parallel(mirrors: List[Tuple[str, str]], max_workers: int = MAX_PARALLEL_MIRRORS) -> List[Tuple[str, str, Optional[int], Optional[str]]]:
    """
    Test mirrors in parallel using ThreadPoolExecutor
    Returns list of (name, url, speed_ms, error_msg) tuples
    """
    logger.info(f"Testing {len(mirrors)} mirrors with {max_workers} parallel workers...")
    
    loop = asyncio.get_event_loop()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all mirror tests
        futures = [
            loop.run_in_executor(executor, test_mirror_speed, mirror)
            for mirror in mirrors
        ]
        
        # Wait for all tests to complete
        results = await asyncio.gather(*futures)
    
    logger.info(f"Mirror testing completed: {len(results)} results")
    return results

def sort_mirrors_by_speed(results: List[Tuple[str, str, Optional[int], Optional[str]]]) -> List[Tuple[str, str, str]]:
    """
    Sort mirrors by speed and format for display
    Returns list of (display_name, url, status) tuples
    """
    working_mirrors = []
    failed_mirrors = []
    
    for name, url, speed_ms, error_msg in results:
        if speed_ms is not None:
            display_name = f"{name} ({speed_ms}ms)"
            working_mirrors.append((display_name, url, "working"))
        else:
            display_name = f"{name} (Failed: {error_msg})"
            failed_mirrors.append((display_name, url, "failed"))
    
    # Sort working mirrors by speed
    working_mirrors.sort(key=lambda x: int(x[0].split('(')[1].split('ms')[0]))
    
    # Combine working + failed mirrors
    return working_mirrors + failed_mirrors

async def get_tested_mirrors() -> List[Tuple[str, str, str]]:
    """
    Get list of tested and sorted mirrors
    Returns list of (display_name, url, status) tuples
    """
    logger.info("Starting comprehensive mirror testing...")
    
    # Test all mirrors in parallel
    results = await test_mirrors_parallel(WORLDWIDE_MIRRORS)
    
    # Sort by speed
    sorted_mirrors = sort_mirrors_by_speed(results)
    
    logger.info(f"Mirror testing complete: {len([m for m in sorted_mirrors if m[2] == 'working'])} working mirrors")
    
    return sorted_mirrors

def get_fastest_mirror(mirrors: List[Tuple[str, str, str]]) -> Optional[Tuple[str, str]]:
    """Get the fastest working mirror"""
    for display_name, url, status in mirrors:
        if status == "working":
            return display_name, url
    return None

# Cache for mirror test results
_mirror_cache = None
_cache_timestamp = 0

async def get_cached_mirrors(cache_duration: int = 300) -> List[Tuple[str, str, str]]:
    """
    Get mirrors with caching (5 minute default cache)
    """
    global _mirror_cache, _cache_timestamp
    
    current_time = time.time()
    
    # Return cached results if still valid
    if _mirror_cache and (current_time - _cache_timestamp) < cache_duration:
        logger.info("Using cached mirror results")
        return _mirror_cache
    
    # Test mirrors and cache results
    _mirror_cache = await get_tested_mirrors()
    _cache_timestamp = current_time
    
    return _mirror_cache
