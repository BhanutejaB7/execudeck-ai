import subprocess
import shutil
import os
import psutil

class TelemetryTracker:
    def __init__(self):
        self.reset()
        
    def reset(self):
        self.session_calls = 0
        self.total_latency = 0.0
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.latencies = []
        self.tokens_per_sec_list = []
        
    def add_call(self, metrics):
        """
        Accumulates metrics from a model call.
        """
        self.session_calls += 1
        self.total_latency += metrics.get("latency_seconds", 0.0)
        self.total_prompt_tokens += metrics.get("prompt_tokens", 0)
        self.total_completion_tokens += metrics.get("completion_tokens", 0)
        self.latencies.append(metrics.get("latency_seconds", 0.0))
        self.tokens_per_sec_list.append(metrics.get("tokens_per_second", 0.0))
        
    def get_session_summary(self):
        """
        Returns average speed and totals.
        """
        avg_tokens_per_sec = 0.0
        if self.tokens_per_sec_list:
            avg_tokens_per_sec = sum(self.tokens_per_sec_list) / len(self.tokens_per_sec_list)
            
        return {
            "calls_count": self.session_calls,
            "total_latency_seconds": round(self.total_latency, 3),
            "total_prompt_tokens": self.total_prompt_tokens,
            "total_completion_tokens": self.total_completion_tokens,
            "avg_tokens_per_second": round(avg_tokens_per_sec, 2)
        }

def get_rocm_gpu_stats():
    """
    Attempts to execute rocm-smi to fetch live AMD GPU statistics.
    Returns:
        dict: GPU stats or indicator string
    """
    # Check if rocm-smi is in the PATH
    rocm_smi_path = shutil.which("rocm-smi")
    if not rocm_smi_path:
        # Check standard Linux ROCm locations
        standard_path = "/opt/rocm/bin/rocm-smi"
        if os.path.exists(standard_path):
            rocm_smi_path = standard_path
            
    if not rocm_smi_path:
        return {"status": "Local Development Mode - GPU unavailable"}
        
    try:
        # Run rocm-smi to query memory info and utilization
        # We can run `rocm-smi --showmeminfo vram --showuse --json` or parse text
        # To make it robust across ROCm versions, let's run standard query:
        result = subprocess.run(
            [rocm_smi_path, "-m", "-u", "--json"], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True, 
            timeout=2.0
        )
        if result.returncode == 0:
            import json
            data = json.loads(result.stdout)
            # vLLM/ROCm JSON formatting can be parsed
            return {"status": "ROCm GPU Connected", "raw_data": data}
    except Exception:
        pass
        
    # Text-based fallback parsing if JSON query failed
    try:
        result = subprocess.run(
            [rocm_smi_path, "--showmeminfo", "vram"], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True, 
            timeout=2.0
        )
        if result.returncode == 0:
            lines = result.stdout.split("\n")
            total_vram = None
            used_vram = None
            for line in lines:
                if "VRAM Total Memory" in line:
                    parts = line.split(":")
                    if len(parts) > 1:
                        total_vram = parts[1].strip()
                if "VRAM Used Memory" in line:
                    parts = line.split(":")
                    if len(parts) > 1:
                        used_vram = parts[1].strip()
            if total_vram and used_vram:
                return {
                    "status": "ROCm GPU Connected",
                    "total_vram": total_vram,
                    "used_vram": used_vram
                }
    except Exception:
        pass
        
    return {"status": "ROCm GPU Detected (rocm-smi query failed)"}

def get_system_telemetry():
    """
    Returns standard system metrics for local fallback reporting.
    """
    cpu_pct = psutil.cpu_percent()
    mem = psutil.virtual_memory()
    return {
        "cpu_usage_percentage": cpu_pct,
        "ram_used_gb": round(mem.used / (1024**3), 2),
        "ram_total_gb": round(mem.total / (1024**3), 2),
        "ram_usage_percentage": mem.percent
    }
