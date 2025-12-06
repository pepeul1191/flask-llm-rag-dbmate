def detect_gpu_libraries():
    """Detecta qué bibliotecas de GPU están disponibles."""
    gpu_libs = []
    
    # Verificar NVIDIA (pynvml)
    try:
        import pynvml
        pynvml.nvmlInit()
        device_count = pynvml.nvmlDeviceGetCount()
        if device_count > 0:
            gpu_libs.append('nvidia')
        pynvml.nvmlShutdown()
    except ImportError:
        pass
    except Exception:
        pass
    
    # Verificar AMD (pyamdgpuinfo o rocm-smi)
    try:
        import subprocess
        result = subprocess.run(['rocm-smi', '--showuse'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            gpu_libs.append('amd')
    except:
        pass
    
    # Verificar Intel (pynvml también puede funcionar para Intel)
    try:
        import GPUtil
        gpus = GPUtil.getGPUs()
        for gpu in gpus:
            if 'intel' in gpu.name.lower():
                gpu_libs.append('intel')
                break
    except:
        pass
    
    return gpu_libs

def get_gpu_info(gpu_libs):
    """Obtiene información de la GPU según las bibliotecas disponibles."""
    gpu_info = {}
    
    if 'nvidia' in gpu_libs:
        try:
            import pynvml
            pynvml.nvmlInit()
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            
            # Uso de GPU
            util = pynvml.nvmlDeviceGetUtilizationRates(handle)
            gpu_info['utilization'] = util.gpu
            
            # Memoria
            mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
            gpu_info['memory_total'] = mem_info.total / (1024 * 1024)  # MB
            gpu_info['memory_used'] = mem_info.used / (1024 * 1024)    # MB
            gpu_info['memory_free'] = mem_info.free / (1024 * 1024)    # MB
            
            # Temperatura
            try:
                temp = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
                gpu_info['temperature'] = temp
            except:
                gpu_info['temperature'] = 0
            
            # Nombre
            gpu_info['name'] = pynvml.nvmlDeviceGetName(handle)
            
            pynvml.nvmlShutdown()
            
        except Exception as e:
            print(f"⚠️  Error obteniendo info NVIDIA: {e}")
    
    elif 'amd' in gpu_libs:
        try:
            import subprocess
            # Usar rocm-smi para AMD
            result = subprocess.run(['rocm-smi', '--showuse', '--showmemuse', '--showtemp'], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'GPU use' in line:
                        parts = line.split()
                        for i, part in enumerate(parts):
                            if part == 'use' and i+1 < len(parts):
                                util = parts[i+1].replace('%', '')
                                try:
                                    gpu_info['utilization'] = float(util)
                                except:
                                    pass
                    
                    elif 'GPU memory use' in line:
                        parts = line.split()
                        for i, part in enumerate(parts):
                            if part == 'use' and i+1 < len(parts):
                                mem = parts[i+1].replace('%', '')
                                try:
                                    gpu_info['memory_percent'] = float(mem)
                                except:
                                    pass
                    
                    elif 'GPU temperature' in line:
                        parts = line.split()
                        for i, part in enumerate(parts):
                            if part == 'temperature' and i+1 < len(parts):
                                temp = parts[i+1].replace('C', '')
                                try:
                                    gpu_info['temperature'] = float(temp)
                                except:
                                    pass
        except Exception as e:
            print(f"⚠️  Error obteniendo info AMD: {e}")
    
    elif 'intel' in gpu_libs:
        try:
            # Intel generalmente usa pynvml también
            import pynvml
            pynvml.nvmlInit()
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            
            util = pynvml.nvmlDeviceGetUtilizationRates(handle)
            gpu_info['utilization'] = util.gpu
            
            mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
            gpu_info['memory_used'] = mem_info.used / (1024 * 1024)
            
            gpu_info['name'] = pynvml.nvmlDeviceGetName(handle)
            
            pynvml.nvmlShutdown()
            
        except Exception as e:
            print(f"⚠️  Error obteniendo info Intel: {e}")
    
    return gpu_info

def print_resumen_metricas(success, total_time, rag_time, parse_time,
                          mem_before, mem_avg, mem_final,
                          cpu_before, cpu_avg, cpu_final,
                          gpu_libs, gpu_util_avg, gpu_mem_avg, gpu_temp_avg,
                          gpu_util_samples, gpu_mem_samples, gpu_temp_samples,
                          num_tables, expected_tables, error_msg):
    """Muestra un resumen detallado de las métricas."""
    
    print(f"\n{'='*60}")
    print("📈 RESUMEN COMPLETO DE MÉTRICAS:")
    print(f"{'='*60}")
    print(f"✅ Éxito: {'SÍ' if success else 'NO'}")
    print(f"⏱️  Tiempo total: {total_time:.2f} ms")
    print(f"🤖 Tiempo RAG: {rag_time:.2f} ms")
    print(f"🔧 Tiempo parsing: {parse_time:.2f} ms")
    
    print(f"\n💾 RAM:")
    print(f"  - Antes RAG:       {mem_before:.2f} MB")
    print(f"  - Promedio durante RAG: {mem_avg:.2f} MB")
    print(f"  - Final:           {mem_final:.2f} MB")
    print(f"  - Δ RAG:           {mem_avg - mem_before:+.2f} MB")
    print(f"  - Δ Total:         {mem_final - mem_before:+.2f} MB")
    
    print(f"\n📈 CPU:")
    print(f"  - Antes RAG:       {cpu_before:.1f}%")
    print(f"  - Promedio durante RAG: {cpu_avg:.1f}%")
    print(f"  - Final:           {cpu_final:.1f}%")
    
    if gpu_libs:
        print(f"\n🎮 GPU ({', '.join(gpu_libs)}):")
        if gpu_util_samples:
            print(f"  - Uso promedio:    {gpu_util_avg:.1f}%")
            print(f"  - Uso máximo:      {max(gpu_util_samples) if gpu_util_samples else 0:.1f}%")
        if gpu_mem_samples:
            print(f"  - Memoria promedio: {gpu_mem_avg:.2f} MB")
            print(f"  - Memoria máxima:   {max(gpu_mem_samples) if gpu_mem_samples else 0:.2f} MB")
        if gpu_temp_samples and gpu_temp_avg > 0:
            print(f"  - Temp promedio:    {gpu_temp_avg:.1f}°C")
            print(f"  - Temp máxima:      {max(gpu_temp_samples) if gpu_temp_samples else 0:.1f}°C")
    
    print(f"\n📊 Tablas: {num_tables}/{expected_tables}")
    
    if not success and error_msg:
        print(f"\n⚠️  ERROR: {error_msg}")
    
    print(f"{'='*60}")