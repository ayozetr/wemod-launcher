# Plan de mejoras — wemod-launcher

> Roadmap de correcciones y refactors para el fork `ayozetr/wemod-launcher`.
> Basado en un análisis exhaustivo módulo a módulo (8 ficheros, ~3.700 líneas)
> con auditoría de arquitectura/seguridad/calidad y verificación adversarial.
>
> **Naturaleza del proyecto:** launcher local instalado voluntariamente, sin
> frontera de confianza ni atacante remoto. Por eso casi ningún hallazgo es una
> *vulnerabilidad* explotable; el valor real está en los **bugs de corrección**
> y en la **fiabilidad**. Donde se marca "seguridad" es endurecimiento, no un
> agujero explotable.

## Estado actual

**✅ TODAS las fases completadas** en la rama `fix/correctness-and-hardening`.
Verificado con `python3 -m py_compile`, `ruff check src/` (0 errores) y
`pytest` (16 tests en verde). Lo único no ejecutable en este entorno es el
flujo end-to-end real (requiere Steam/Proton/Wine) y `wemod.bat` (corre dentro
del prefijo Wine); sus cambios se revisaron por diff.

| Fase | Descripción | Estado |
|------|-------------|--------|
| 0 | Refactor `paths.py` (dedup boilerplate `SCRIPT_PATH` en 7 módulos) | ✅ HECHO |
| 1 | Bugs de corrección (10 + menores) | ✅ HECHO |
| 2 | Endurecer subprocess/shell y descargas | ✅ HECHO |
| 3 | Refactor: `consts.py` sin efectos en import-time | ✅ HECHO |
| 4 | Escritura atómica de `wemod.conf` | ✅ HECHO |
| 5 | `wemod.bat`: quoting y cuelgues | ✅ HECHO |
| 6 | Tests (`pytest`) + `ruff` en CI | ✅ HECHO |

> Nota sobre alcance: el refactor "config global → objeto inyectable" (Fase 4)
> se hizo de forma conservadora (escritura atómica), no reescribiendo la API en
> 6 módulos, por riesgo sin tests E2E. Algunos bugs menores de robustez listados
> abajo (p. ej. `deref` con symlinks relativos, `commonprefix` por caracteres,
> validación de `assets`/`net[0]`) quedan como mejoras opcionales futuras.

**Limpieza de ramas (hecha):** se borraron las 19 ramas heredadas del upstream
en `origin`; queda solo `main`. El remote `upstream` apunta a
`https://github.com/DeckCheatz/wemod-launcher.git` para recuperar lo que sea
con `git fetch upstream`.

---

## Fase 0 — `paths.py` (HECHO)

Se creó `src/paths.py` con la resolución PyInstaller-aware de `SCRIPT_PATH`,
`SCRIPT_IMP_FILE` y `SCRIPT_BASE`, y se reemplazó el bloque duplicado
(`if getattr(sys, "frozen", ...)`) en los 7 módulos por `from paths import ...`.
Se eliminó `import sys` donde quedó huérfano (verificado por grep).
Comportamiento idéntico (los valores coinciden; ver verificación).

---

## Fase 1 — Bugs de corrección

Bugs confirmados leyendo el código (varios reproducidos con Python). Cambios
quirúrgicos, bajo riesgo.

| # | Archivo:línea | Bug | Fix |
|---|---|---|---|
| 1 | `corenodep.py:110-117` (`parse_version`) | **AttributeError reproducido**: con versión sin *minor* (`'v9'`, `'7'`, `'GE-Proton9'`) se hace `minornumber = 0` (int) y luego `len(minornumber.lstrip("0"))` → `'int' has no attribute 'lstrip'`. | Inicializar `minornumber = "0"` (string), o gestionar `None` devolviendo `[major, 0]` sin llamar `.lstrip` sobre un int. Idealmente reescribir el parseo a tuplas de int. |
| 2 | `constutils.py:264` (`scanfolderforversions`) | Typo `os.makedirs(prefixesfolder, exists_ok=True)` → `TypeError` (kwarg correcto: `exist_ok`). | `exist_ok=True`. |
| 3 | `mainutils.py:289` (`get_dotnet48`) | URL de .NET 4.8 truncada: termina en `ndp48-x86-x64-allos-enu.` sin `exe`. Descarga inválida. | Añadir `exe`: `...allos-enu.exe`. |
| 4 | `setup.py:403-404` (`setup_main`) | `shutil.rmtree(winetricks)` sobre un **archivo** → `NotADirectoryError` (rmtree solo borra directorios). Rompe `FORCE_UPDATE_WEMOD=1`. | `os.remove(winetricks)`. |
| 5 | `wemod.py:963,967` (`run`) | `PROTON = PROTON_CMD[0]` es un **string**; luego `PROTON[(fnr_p + 1)].find(".")` indexa un *carácter* de la ruta, no el siguiente argumento. Bug lógico en detección de custom runner. | Usar `PROTON_CMD[(fnr_p + 1)].find(".")` (la lista), igual que la rama paralela con `ARGS[(fnr + 1)]`. Validar longitud antes. |
| 6 | `wemod.py:871` (`run`) | `os.getenv("STEAM_COMPAT_TOOL_PATHS").split(os.pathsep)` → `AttributeError` si la variable no está (ejecución fuera del runtime de Steam o comando manual). | `os.getenv("STEAM_COMPAT_TOOL_PATHS", "").split(os.pathsep)` y filtrar vacíos. |
| 7 | `setup.py:203-256` (`venv_manager`) | Si `check_dependencies` devuelve `True` (deps ya instaladas), no hay `return` explícito → devuelve `None` en vez de `[]`. Contrato `List[Optional[str]]` violado. | Añadir `return []` al final / cuando las deps ya están. |
| 8 | `setup.py:330-333` (`self_update`) | `chmod -R ug+x *.py wemod.bat` por subprocess **sin shell**: el glob `*.py` no se expande, se pasa literal. El `chmod` es inoperante salvo para `wemod.bat`. | Expandir el glob en Python (`glob.glob`) y pasar la lista de ficheros reales. |
| 9 | `mainutils.py:480-483` (`copy_folder_with_progress`) | Títulos de ventana **intercambiados**: con `zipup=True` muestra "Copying Prefix" y con `zipup=False` "Zipping File". | Intercambiar: `zipup` → "Zipping…", else → "Copying…". |
| 10 | `wemod.py:872-888` (`run`) | Dos bucles de búsqueda del tool-path **idénticos** y consecutivos; el primero (con `if fnr <= 0`) es código muerto redundante. | Eliminar el bloque duplicado (líneas 872-879). |

**Otros bugs/robustez menores detectados (opcionales):**
- `consts.py:88-92` (`get_compat`): `os.path.dirname(wine)` se evalúa cuando
  `wine = os.getenv("WINE")` puede ser `None` → `TypeError`. Proteger con `if wine` antes.
- `consts.py:96`: separador `':'` hardcodeado en vez de `os.pathsep`.
- `mainutils.py:78-80,97-99...` (`find_closest_compatible_release`):
  `release["assets"][0]` sin validar lista vacía → `IndexError/KeyError`.
- `mainutils.py:309-316,329` (`deref`): `os.readlink` puede dar ruta **relativa**;
  `os.path.exists(src)`/`open(src)` la evalúan respecto al cwd, no al dir del symlink.
  Resolver con `os.path.join(os.path.dirname(target), src)` o `os.path.realpath`.
- `mainutils.py:435-445`: filtro por `os.path.commonprefix` es por **caracteres**,
  no por componentes de ruta (falsos positivos). Comparar por segmentos.
- `setup.py:127,156` (`get_wemod_exe_url`/`unpack_wemod`): `raw["architecture"]["64bit"]["url"]`
  y `net[0]` sin validar claves/lista vacía.
- `corenodep.py:33-37` (`check_dependencies`): asume nombre paquete == nombre módulo
  (falla con `PyYAML`→`yaml`, etc.). Irrelevante hoy (solo `FreeSimpleGUI`), pero frágil.
- `coreutils.py:287-289` (`pip`): `show_message(...)` sin el argumento `title` (posicional
  obligatorio) → `TypeError` si se alcanza esa rama de error.
- `coreutils.py:544` (`script_manager`): comparación de versión con `float(...)` rompe
  con esquemas de 2 puntos (`1.5.4`). 
- `wemod.py:1183`: variable mal escrita `RESPONCE` (typo, cosmético).

---

## Fase 2 — Endurecer subprocess/shell y descargas

Patrón sistémico (12 sitios). No es explotable (entradas controladas por el
propio usuario local) pero **rompe con rutas que contengan espacios o `'`** y es
mala práctica. Crear un helper y migrar todos los call-sites.

- **`os.system(f"xdg-open '{ruta}'")`** → `subprocess.run(["xdg-open", ruta])`:
  - `coreutils.py:77` (`log`), `constutils.py:304` (`scanfolderforversions`),
    `wemod.py:218-220` (`syncwemod`).
- **`shell=True` con interpolación** → listas de argumentos:
  - `coreutils.py:253-258,271-276,295-300,339-344` (`pip`): construir `[pip, *command.split()]`
    o usar `shlex.split`.
  - `mainutils.py:178` (`popup_execute`): `sp.Popen(command, shell=True)`. Los callers
    (`constutils.winetricks/wine`) construyen `export PATH=... && wine ...`. Migrar a
    pasar `env=` a `Popen` y la lista de args, en vez de un string de shell.
  - `constutils.py:325` (`f"sh -c 'chmod +x {winetricks_sh}'"`) → `os.chmod(winetricks_sh, ...)`.
- **Descargas sin verificar `status_code`**:
  - `mainutils.py:214-227` (`download_progress`): comprobar `response.status_code == 200`
    antes de escribir; si no, no renombrar el `.tmp` a destino final.
  - `constutils.py:318-322` (`winetricks`): validar respuesta antes de escribir el binario.
- **Excepciones tragadas (`except ...: pass`, ~14 sitios)**: como mínimo `log(f"...: {e}")`.
  Capturar tipos concretos (`OSError`, `FileNotFoundError`). Sitios: `constutils.py:66-97,296,401-407`,
  `consts.py:56-57` (`getbatcmd`), `corenodep.py:82` (`read_file`), `mainutils.py` varios.

---

## Fase 3 — `consts.py` sin efectos en import-time (refactor)

**Problema:** importar `consts` ejecuta `getbatcmd()` (descarga `wemod.bat`),
`get_compat()` (muta `os.environ`, puede hacer `exit_with_message`) y crea
directorios. Hace los módulos no testeables y el orden de import de `wemod.py`
"load-bearing".

**Fix (preserva comportamiento):**
1. En `consts.py`: dejar las constantes (`BAT_COMMAND`, `BASE_STEAM_COMPAT`,
   `STEAM_COMPAT_FOLDER`, `SCAN_FOLDER`, `WINETRICKS`, `WINEPREFIX`, `INIT_FILE`)
   inicializadas a `None` y mover el trabajo a una función `init_consts()` que las
   rellene con `global`.
2. En `wemod.py`, en la sección **posterior** al primer bloque `__main__` (justo
   donde hoy está `from consts import ...`, línea ~118):
   ```python
   import consts
   consts.init_consts()
   from consts import (BASE_STEAM_COMPAT, BAT_COMMAND, INIT_FILE,
                       STEAM_COMPAT_FOLDER, WINEPREFIX)
   from constutils import (...)
   ```
   `constutils` se importa después, así que su `from consts import ...` captura los
   valores ya inicializados. **Verificado en el análisis:** ningún módulo del
   bootstrap (`corenodep`/`coreutils`/`mainutils`/`setup`) importa `consts`, por lo
   que el efecto sigue ocurriendo en el mismo punto del flujo, pero ahora explícito.

> Resultado: `import consts` pasa a ser inocuo (testeable); el trabajo solo corre
> al llamar `init_consts()`.

---

## Fase 4 — Escritura atómica de `wemod.conf`

`corenodep.py:74-75` (`save_conf_setting`): `open(CONFIG_PATH, "w")` + `CONFIG.write`
reescribe el fichero completo sin atomicidad → corrupción si el proceso muere o hay
dos instancias (Steam relanza).

**Fix:** escribir a `CONFIG_PATH + ".tmp"` y `os.replace(tmp, CONFIG_PATH)` (rename
atómico en POSIX). Mantener la API `load/save_conf_setting` intacta.

> Nota: el refactor "config global → objeto inyectable" se descarta deliberadamente:
> reescribiría la API en 6 módulos con alto riesgo y sin tests E2E. La escritura
> atómica arregla el bug real (corrupción) sin tocar la API.

También en `syncwemod` (`wemod.py:391-394`): `shutil.rmtree(WeModData)` + `copytree`
sin backup. La rama requiere consentimiento explícito del usuario y los datos son
regenerables (re-login), pero conviene copiar a un temporal y `os.replace` solo si
la copia tuvo éxito, conservando un `.bak`.

---

## Fase 5 — `wemod.bat`

- **Quoting:** entrecomillar todas las rutas (`start`, `type`, `del`, `if exist`,
  `taskkill`) — hoy rompe con rutas que tengan espacios. Usar
  `SETLOCAL EnableDelayedExpansion` en los bloques con `SET` dentro de `IF/ELSE`
  (líneas 7-11).
- **`pause` que cuelga** (línea 45): lanzado por Steam/Proton sin terminal cuelga
  para siempre. Sustituir por salida con código de error + log.
- **PID:** se queda con el último de varios procesos `WeMod.exe` homónimos → puede
  dejar huérfanos. Revisar la selección del PID o matar el árbol.
- **`:WaitUser`** (líneas 77-79): sin timeout; si el lado Python muere sin borrar
  `return.tmp`, se bloquea indefinidamente. Añadir contador/timeout.
- `ping localhost -n N` como sleep → `timeout /t N` donde sea viable.

---

## Fase 6 — Tests y CI

- **`pytest`** sobre funciones puras (sin I/O), que es donde está la lógica frágil:
  `parse_version`, `winpath`, `split_list_by_delimiter`, `join_lists_with_delimiter`,
  `find_closest_compatible_release`, `contains_url_protocol`, `is_exe_or_forced`.
  Casos clave para `parse_version`: `'7'`, `'v9'`, `'8.0'`, `'1.2.3'`,
  `'GE-Proton9-20'`, `'PfxVer8.26'`, `'GE-Proton'` (sin número).
  *(La Fase 3 es prerequisito para poder importar módulos que dependen de `consts`.)*
- **`ruff`** en `.github/workflows/black.yml` junto a `black`: cazaría imports
  muertos (`popup_execute` en `wemod.py:42`, `join_lists_with_delimiter` en
  `coreutils.py`), `== None` (18 sitios), bare-except.
- **`mypy`** opcional (`--strict` es agresivo para esta base).

**Nota sobre el CI actual (`black.yml`):** auto-incrementa la versión con aritmética
flotante (`ver + 0.001`) y hace `git commit --amend` + `git push --force`
suplantando al autor del último commit; usa `actions/checkout@v2` (Node 16, EOL).
Conviene revisarlo si se adopta este flujo en el fork.

---

## Cómo continuar

1. Trabajar sobre la rama `fix/correctness-and-hardening`.
2. Ir fase por fase; tras cada una: `python3 -m py_compile src/*.py` y (Fase 6)
   `pytest`.
3. Verificación rápida del bug #1 (debe dejar de crashear tras el fix):
   ```bash
   cd src && python3 -c "import corenodep; print(corenodep.parse_version('v9'))"
   ```
4. Para recuperar trabajo del upstream: `git fetch upstream && git log upstream/main`.
