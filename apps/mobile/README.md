# UnderNight Mobile

## Backend API

La app móvil usa `EXPO_PUBLIC_API_URL` para conectarse al backend FastAPI.

### iOS Simulator

```bash
EXPO_PUBLIC_API_URL=http://localhost:8000 npm run ios
```

### Dispositivo físico

Obtén la IP local del Mac:

```bash
ipconfig getifaddr en0
```

Luego inicia Expo apuntando a esa IP:

```bash
EXPO_PUBLIC_API_URL=http://<MAC_IP>:8000 npm run start
```

El backend debe estar escuchando en `0.0.0.0:8000` para que otros dispositivos de la red puedan conectarse.
