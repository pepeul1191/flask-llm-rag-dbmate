1. Instalar controladores específicos para Quadro T1000
bash
# Actualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar controladores recomendados para tu GPU
sudo ubuntu-drivers devices

# Instalar el controlador recomendado (generalmente el más reciente compatible)
sudo apt install nvidia-driver-535

# O si quieres la versión más estable
sudo apt install nvidia-driver-470
2. Para laptops con gráficos híbridos (más común)
bash
# Instalar prime-select para manejar gráficos híbridos
sudo apt install nvidia-prime

# Configurar para usar NVIDIA
sudo prime-select nvidia

# Verificar la configuración
prime-select query
3. Si usas Secure Boot (muy importante en laptops)
bash
# Verificar estado de Secure Boot
mokutil --sb-state

# Si Secure Boot está activado, necesitarás:
sudo apt install dkms
sudo mokutil --disable-validation
4. Reiniciar y verificar
bash
# Reiniciar el sistema
sudo reboot

# Después del reinicio, verificar
nvidia-smi

watch -n 1 nvidia-smi

# Deberías ver algo como:
# +---------------------------------------------------------------------------------------+
# | NVIDIA-SMI 535.161.07   Driver Version: 535.161.07   CUDA Version: 12.2     |
# |-----------------------------------------+----------------------+----------------------+
# | GPU  Name                 Persistence-M | Bus-Id        Disp.A | Volatile Uncorr. ECC |
# | Fan  Temp   Perf          Pwr:Usage/Cap |         Memory-Usage | GPU-Util  Compute M. |
# |                                         |                      |               MIG M. |
# |=========================================+======================+======================|
# |   0  Quadro T1000 Mobile           Off  | 00000000:01:00.0 Off |                  N/A |