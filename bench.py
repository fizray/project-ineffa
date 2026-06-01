import os
import time
import glob
import sys
import psutil
import numpy as np
import cv2
import onnxruntime as ort
import yaml
from pathlib import Path

def load_img(path, shape):
    im = cv2.imread(path)
    if im is None:
        return None
    im = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)
    
    # shape is [N, C, H, W]
    # cv2.resize expects (width, height) -> (W, H)
    h = shape[2]
    w = shape[3]
    
    im = cv2.resize(im, (w, h))
    im = im.astype(np.float32) / 255.0
    im = np.transpose(im, (2,0,1))[None,...]  # NCHW
    return im

# Global settings
SETTINGS = {
    "model": "models/2.7_80x80_MiniFASNetV2.onnx",
    "input_dir": None,
    "runs": 200,
    "warmup": 20,
    "threads": 4,
    "batch_size": 1,
    "mode": "Custom", # Detection, Recognition, Liveness, Custom
    "config": {},
    "provider": "CPU" # CPU, GPU
}

def load_config():
    if os.path.exists("config.yaml"):
        with open("config.yaml", "r") as f:
            SETTINGS["config"] = yaml.safe_load(f)
    else:
        print("\033[91m[WARN] config.yaml not found!\033[0m")

def resolve_model_path(mode):
    cfg = SETTINGS["config"]
    home = Path.home()
    
    if mode == "Liveness":
        return cfg.get("liveness", {}).get("model_path", "")
        
    elif mode == "Detection":
        name = cfg.get("detection", {}).get("model_name", "buffalo_l")
        # InsightFace default paths
        if name == "buffalo_l":
            return str(home / ".insightface" / "models" / "buffalo_l" / "det_10g.onnx")
        elif name == "buffalo_s":
            return str(home / ".insightface" / "models" / "buffalo_s" / "det_10g.onnx")
            
    elif mode == "Recognition":
        name = cfg.get("recognition", {}).get("model_name", "buffalo_l")
        if name == "buffalo_l":
            return str(home / ".insightface" / "models" / "buffalo_l" / "w600k_r50.onnx")
        elif name == "buffalo_s":
            return str(home / ".insightface" / "models" / "buffalo_s" / "w600k_mbf.onnx")
            
    return ""

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    print("\033[96m==================================================\033[0m")
    print("\033[1m          BENCHMARK TOOL (CPU/GPU)               \033[0m")
    print("\033[96m==================================================\033[0m")

def get_providers():
    if SETTINGS["provider"] == "GPU":
        return ["CUDAExecutionProvider", "CPUExecutionProvider"]
    return ["CPUExecutionProvider"]

def get_model_input_shape(model_path):
    try:
        # Create a dummy session just to get input shape
        sess = ort.InferenceSession(model_path, providers=get_providers())
        inp = sess.get_inputs()[0]
        return inp.shape
    except Exception as e:
        print(f"\033[91mError reading model: {e}\033[0m")
        return None

def run_benchmark():
    model_path = SETTINGS["model"]
    if not os.path.exists(model_path):
        print(f"\n\033[91m[ERROR] Model file not found: {model_path}\033[0m")
        input("Press Enter to continue...")
        return

    print(f"\n\033[93m[INFO] Initializing Benchmark...\033[0m")
    print(f"  Model: {model_path}")
    print(f"  Provider: {SETTINGS['provider']}")
    print(f"  Threads: {SETTINGS['threads']}")
    
    # Set Environment Variables for Threads
    os.environ["OMP_NUM_THREADS"] = str(SETTINGS["threads"])
    
    try:
        so = ort.SessionOptions()
        so.intra_op_num_threads = SETTINGS["threads"]
        so.inter_op_num_threads = 1
        so.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        
        sess = ort.InferenceSession(model_path, sess_options=so, providers=get_providers())
    except Exception as e:
        print(f"\033[91mFailed to load model: {e}\033[0m")
        input("Press Enter to continue...")
        return

    inp = sess.get_inputs()[0]
    shape = list(inp.shape)
    
    # Handle dynamic shapes
    # Default to 1 for batch
    if shape[0] is None or not isinstance(shape[0], int):
        shape[0] = 1
        
    # Default to 640 for spatial dims if None (common for detection)
    # For recognition (112x112), they are usually fixed in the model, so this won't trigger.
    if len(shape) >= 4:
        if shape[2] is None or not isinstance(shape[2], int): shape[2] = 640
        if shape[3] is None or not isinstance(shape[3], int): shape[3] = 640
    
    # Prepare Data
    print("\033[93m[INFO] Preparing Data...\033[0m")
    data = None
    target_batch = SETTINGS["batch_size"]
    
    if SETTINGS["input_dir"] and os.path.exists(SETTINGS["input_dir"]):
        files = glob.glob(os.path.join(SETTINGS["input_dir"], "*.jpg")) + \
                glob.glob(os.path.join(SETTINGS["input_dir"], "*.png")) + \
                glob.glob(os.path.join(SETTINGS["input_dir"], "*.jpeg"))
        if files:
            print(f"  Found {len(files)} images in {SETTINGS['input_dir']}")
            imgs = []
            # Load enough images to fill batch or loop
            needed = target_batch
            loaded_count = 0
            
            # Cycle through files if we need more than we have
            while len(imgs) < target_batch and files:
                for f in files:
                    if len(imgs) >= target_batch: break
                    img = load_img(f, shape)
                    if img is not None:
                        imgs.append(img)
            
            if imgs:
                # If we still don't have enough (e.g. no valid images), this will be handled below
                data = np.concatenate(imgs[:target_batch], axis=0)
    
    if data is None:
        print(f"  Using Synthetic Data (Random Noise) - Batch Size: {target_batch}")
        h, w = shape[2], shape[3]
        data = np.random.rand(target_batch, 3, h, w).astype(np.float32)
    elif data.shape[0] != target_batch:
        # Fallback if we couldn't load enough real images (shouldn't happen with the loop above unless 0 files)
        print(f"  [WARN] Could not load enough images for batch {target_batch}. Using synthetic fill.")
        current = data.shape[0]
        missing = target_batch - current
        h, w = shape[2], shape[3]
        fill = np.random.rand(missing, 3, h, w).astype(np.float32)
        data = np.concatenate([data, fill], axis=0)

    print(f"  Input Data Shape: {data.shape}")

    # Warmup
    print(f"\033[93m[INFO] Warming up ({SETTINGS['warmup']} runs)...\033[0m")
    for _ in range(SETTINGS["warmup"]):
        sess.run(None, {inp.name: data})

    # Benchmark
    print(f"\033[92m[GO] Running Benchmark ({SETTINGS['runs']} runs)...\033[0m")
    times = []
    cpu_samples = []
    proc = psutil.Process()
    
    t_start_total = time.perf_counter()
    
    for i in range(SETTINGS["runs"]):
        # Simple progress bar
        if i % 10 == 0:
            sys.stdout.write(f"\r  Progress: {i}/{SETTINGS['runs']}")
            sys.stdout.flush()
            
        t0 = time.perf_counter()
        sess.run(None, {inp.name: data})
        t1 = time.perf_counter()
        
        times.append(t1 - t0)
        cpu_samples.append(proc.cpu_percent(interval=None))
    
    t_end_total = time.perf_counter()
    print(f"\r  Progress: {SETTINGS['runs']}/{SETTINGS['runs']} [DONE]")

    # Analysis
    times_ms = np.array(times) * 1000
    total_time = t_end_total - t_start_total
    throughput = (SETTINGS["runs"] * data.shape[0]) / total_time
    
    mean_lat = np.mean(times_ms)
    median_lat = np.median(times_ms)
    p95_lat = np.percentile(times_ms, 95)
    p99_lat = np.percentile(times_ms, 99)
    min_lat = np.min(times_ms)
    max_lat = np.max(times_ms)
    avg_cpu = np.mean(cpu_samples)

    # Report
    print("\n\033[96m" + "="*50)
    print(f"             BENCHMARK RESULTS             ")
    print("="*50 + "\033[0m")
    print(f" Model       : {os.path.basename(model_path)}")
    print(f" Input Shape : {shape}")
    print(f" Batch Size  : {SETTINGS['batch_size']}")
    print(f" Threads     : {SETTINGS['threads']}")
    print(f" Total Time  : {total_time:.3f} s")
    print("-" * 50)
    print(f"\033[1m Performance Metrics:\033[0m")
    print(f"  Throughput : \033[92m{throughput:.2f} img/sec\033[0m")
    print(f"  Avg CPU    : {avg_cpu:.1f}%")
    print("-" * 50)
    print(f"\033[1m Latency (ms):\033[0m")
    print(f"  Mean       : {mean_lat:.2f} ms")
    print(f"  Median     : {median_lat:.2f} ms")
    print(f"  95th %ile  : {p95_lat:.2f} ms")
    print(f"  99th %ile  : {p99_lat:.2f} ms")
    print(f"  Min / Max  : {min_lat:.2f} / {max_lat:.2f} ms")
    print("="*50)
    
    input("\nPress Enter to return to menu...")

def change_model():
    print("\n\033[93m[INFO] Scanning for ONNX models in 'models/'...\033[0m")
    models = glob.glob("models/*.onnx") + glob.glob("models/**/*.onnx", recursive=True)
    
    if not models:
        print("No models found in 'models/' directory.")
        path = input("Enter full path to .onnx file: ").strip()
        if os.path.exists(path):
            SETTINGS["model"] = path
    else:
        print("Found models:")
        for i, m in enumerate(models):
            print(f"  {i+1}. {m}")
        print(f"  0. Enter custom path")
        
        choice = input("Select model (0-N): ").strip()
        if choice.isdigit():
            idx = int(choice)
            if idx == 0:
                path = input("Enter full path to .onnx file: ").strip()
                if os.path.exists(path):
                    SETTINGS["model"] = path
            elif 1 <= idx <= len(models):
                SETTINGS["model"] = models[idx-1]

def change_input_dir():
    print(f"\nCurrent Input Dir: {SETTINGS['input_dir']}")
    new_dir = input("Enter new directory path (or leave empty for Synthetic): ").strip()
    if new_dir == "":
        SETTINGS["input_dir"] = None
    elif os.path.exists(new_dir):
        SETTINGS["input_dir"] = new_dir
    else:
        print("\033[91mDirectory does not exist!\033[0m")
        time.sleep(1)

def change_threads():
    print(f"\nCurrent Threads: {SETTINGS['threads']}")
    try:
        val = int(input("Enter number of threads (1-64): ").strip())
        if 1 <= val <= 64:
            SETTINGS["threads"] = val
    except ValueError:
        pass

def change_runs():
    print(f"\nCurrent Runs: {SETTINGS['runs']} | Warmup: {SETTINGS['warmup']}")
    try:
        r = input(f"Enter Runs [{SETTINGS['runs']}]: ").strip()
        w = input(f"Enter Warmup [{SETTINGS['warmup']}]: ").strip()
        if r: SETTINGS["runs"] = int(r)
        if w: SETTINGS["warmup"] = int(w)
    except ValueError:
        pass

def change_batch_size():
    print(f"\nCurrent Batch Size: {SETTINGS['batch_size']}")
    try:
        val = int(input("Enter Batch Size (1-128): ").strip())
        if 1 <= val <= 128:
            SETTINGS["batch_size"] = val
    except ValueError:
        pass

def change_provider():
    print(f"\nCurrent Provider: {SETTINGS['provider']}")
    print("Available Providers:")
    available = ort.get_available_providers()
    for p in available:
        print(f"  - {p}")
        
    print("\nSelect Provider:")
    print("  1. CPU")
    print("  2. GPU (CUDA)")
    
    choice = input("Select option (1-2): ").strip()
    if choice == '1':
        SETTINGS["provider"] = "CPU"
    elif choice == '2':
        if "CUDAExecutionProvider" in available:
            SETTINGS["provider"] = "GPU"
        else:
            print("\033[91mCUDA Provider not available!\033[0m")
            time.sleep(1)

def change_mode():
    print("\nSelect Benchmark Mode:")
    print("  1. Detection (from config)")
    print("  2. Recognition (from config)")
    print("  3. Liveness (from config)")
    print("  4. Custom (Manual Path)")
    
    choice = input("Select mode (1-4): ").strip()
    
    new_mode = None
    if choice == '1': new_mode = "Detection"
    elif choice == '2': new_mode = "Recognition"
    elif choice == '3': new_mode = "Liveness"
    elif choice == '4': new_mode = "Custom"
    
    if new_mode:
        SETTINGS["mode"] = new_mode
        if new_mode != "Custom":
            path = resolve_model_path(new_mode)
            if path and os.path.exists(path):
                SETTINGS["model"] = path
                print(f"\033[92mModel set to: {path}\033[0m")
            else:
                print(f"\033[91mCould not resolve path for {new_mode} or file not found: {path}\033[0m")
                if path: print(f"Checked path: {path}")
                time.sleep(2)
        else:
            change_model()

def main():
    load_config()
    while True:
        clear_screen()
        print_header()
        
        # Status Panel
        print(f" \033[1mCurrent Configuration:\033[0m")
        print(f"  [Mode]       : \033[95m{SETTINGS['mode']}\033[0m")
        print(f"  [M] Model    : \033[96m{SETTINGS['model']}\033[0m")
        inp_str = SETTINGS['input_dir'] if SETTINGS['input_dir'] else "Synthetic (Random Noise)"
        print(f"  [I] Input    : {inp_str}")
        print(f"  [B] Batch    : \033[93m{SETTINGS['batch_size']}\033[0m")
        print(f"  [P] Provider : \033[95m{SETTINGS['provider']}\033[0m")
        print(f"  [T] Threads  : \033[93m{SETTINGS['threads']}\033[0m")
        print(f"  [R] Runs     : {SETTINGS['runs']} (Warmup: {SETTINGS['warmup']})")
        print("-" * 50)
        
        print("1. \033[92mRun Benchmark\033[0m")
        print("2. Change Benchmark Mode")
        print("3. Change Model Path (Custom)")
        print("4. Change Input Directory")
        print("5. Set Threads")
        print("6. Set Batch Size")
        print("7. Set Runs & Warmup")
        print("8. Change Provider (CPU/GPU)")
        print("0. Exit")
        print("=" * 50)
        
        try:
            choice = input("Select option: ").strip()
        except EOFError:
            print("\nNo input available. Exiting benchmark.")
            sys.exit(0)
        
        if choice == '1':
            run_benchmark()
        elif choice == '2':
            change_mode()
        elif choice == '3':
            SETTINGS["mode"] = "Custom"
            change_model()
        elif choice == '4':
            change_input_dir()
        elif choice == '5':
            change_threads()
        elif choice == '6':
            change_batch_size()
        elif choice == '7':
            change_runs()
        elif choice == '8':
            change_provider()
        elif choice == '0':
            print("\nGoodbye!")
            sys.exit(0)
        else:
            print("\nInvalid option!")
            time.sleep(0.5)

if __name__=="__main__":
    main()
