/**
 * Helper para detectar y usar el comando correcto de Python
 * Funciona en Windows, Linux y Mac
 */
const { execSync } = require('child_process');
const os = require('os');

let pythonCommand = null;

/**
 * Detecta el comando correcto de Python disponible en el sistema
 * @returns {string} - Comando de Python ('python', 'python3', 'py', etc.)
 */
function detectPythonCommand() {
  if (pythonCommand) {
    return pythonCommand;
  }

  const commands = process.platform === 'win32' 
    ? ['python', 'py', 'python3']  // Windows: probar python primero
    : ['python3', 'python'];        // Linux/Mac: probar python3 primero

  for (const cmd of commands) {
    try {
      // Verificar que el comando existe y funciona
      execSync(`${cmd} --version`, { stdio: 'ignore', timeout: 2000 });
      pythonCommand = cmd;
      console.log(`Python detectado: ${cmd}`);
      return cmd;
    } catch (err) {
      // Comando no disponible, probar siguiente
      continue;
    }
  }

  // Si no se encuentra ningún comando
  throw new Error(
    'Python no encontrado. Por favor instala Python 3.7 o superior.\n' +
    'Windows: https://www.python.org/downloads/\n' +
    'Asegúrate de marcar "Add Python to PATH" durante la instalación.'
  );
}

/**
 * Obtiene el comando de Python (con caché)
 * @returns {string}
 */
function getPythonCommand() {
  return detectPythonCommand();
}

/**
 * Verifica que Python está instalado y disponible
 * @returns {boolean}
 */
function isPythonAvailable() {
  try {
    detectPythonCommand();
    return true;
  } catch (err) {
    return false;
  }
}

module.exports = {
  getPythonCommand,
  detectPythonCommand,
  isPythonAvailable
};








