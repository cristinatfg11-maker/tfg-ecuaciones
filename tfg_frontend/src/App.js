// Nombre de archivo: src/App.js
// Versión: UPDATE_FINAL_SCREEN_RANKING_V4.0

import React, { useState, useEffect } from 'react'; 
import './App.css'; 

// Pasos del Flujo Nuevo
const STEP_LOGIN = 'STEP_LOGIN';
const STEP_MODO = 'STEP_MODO'; 
const STEP_CLASIFICAR_JUEGO = 'STEP_CLASIFICAR_JUEGO'; 
const STEP_RESOLVER = 'STEP_RESOLVER'; 
const STEP_FINAL = 'STEP_FINAL'; // NUEVO PASO: Pantalla de resultados y ranking

const runMathJax = () => {
  if (window.MathJax && window.MathJax.typesetPromise) {
    window.MathJax.typesetPromise().catch(err => console.error("Error MathJax:", err));
  }
};

function App() {
  const [currentStep, setCurrentStep] = useState(STEP_LOGIN); 
  const [error, setError] = useState('');

  // --- USUARIO ---
  const [usuario, setUsuario] = useState(null); 
  const [authMode, setAuthMode] = useState('login'); 
  const [authData, setAuthData] = useState({ username: '', password: '', new_password: '' });
  const [puntuacionAcumulada, setPuntuacionAcumulada] = useState(0); 

  // --- ESTADOS DEL JUEGO ---
  const [modoSeleccionado, setModoSeleccionado] = useState(''); 
  const [ejercicioJuego, setEjercicioJuego] = useState(null); 
  const [faseClasificacion, setFaseClasificacion] = useState(1); 
  const [feedbackClasificacion, setFeedbackClasificacion] = useState('');
  const [cargandoEjercicio, setCargandoEjercicio] = useState(false); 
  const [rankingData, setRankingData] = useState([]); // NUEVO: Datos del ranking

  // --- VARIABLES NECESARIAS ---
  const [modeloEncontrado, setModeloEncontrado] = useState(null);
  const [listaModelosDisponibles, setListaModelosDisponibles] = useState([]); 
  const [listaEjercicios, setListaEjercicios] = useState([]); 

  // --- ESTADOS RESOLUCIÓN ---
  const [ecuacionActual, setEcuacionActual] = useState('');
  const [mensajeResultado, setMensajeResultado] = useState('');
  const [pasosEntrenamiento, setPasosEntrenamiento] = useState([]);
  const [solucionEntrenamiento, setSolucionEntrenamiento] = useState(''); 
  const [modoPruebaActivo, setModoPruebaActivo] = useState(false);
  const [puntosEjercicio, setPuntosEjercicio] = useState(10);
  const [respuestaEstudiante, setRespuestaEstudiante] = useState('');
  const [solucionOculta, setSolucionOculta] = useState(''); 
  const [solucionFinalLatex, setSolucionFinalLatex] = useState(''); 
  const [pasosCompletosOcultos, setPasosCompletosOcultos] = useState([]); 
  const [pasosReveladosCount, setPasosReveladosCount] = useState(0); 
  const [mostrarSolucionFinal, setMostrarSolucionFinal] = useState(false); 
  const [preguntas, setPreguntas] = useState({}); 

  useEffect(() => {
    if (!cargandoEjercicio) {
        setTimeout(runMathJax, 50); 
    }
    
    // Si entramos a la pantalla final, cargamos el ranking
    if (currentStep === STEP_FINAL) {
        cargarRanking();
    }
  }, [
      currentStep, 
      ejercicioJuego, 
      mensajeResultado, 
      error, 
      mostrarSolucionFinal, 
      pasosReveladosCount, 
      faseClasificacion,
      feedbackClasificacion,
      cargandoEjercicio,
      respuestaEstudiante,
      puntosEjercicio 
  ]);

  const cargarRanking = async () => {
      try {
          const res = await fetch('http://127.0.0.1:8000/api/ranking/');
          if (res.ok) {
              const data = await res.json();
              setRankingData(data.ranking);
          }
      } catch (err) { console.error("Error cargando ranking", err); }
  };

  // --------------------------------------------------------------------------------
  // 1. AUTENTICACIÓN
  // --------------------------------------------------------------------------------
  const handleAuthSubmit = async (e) => {
    e.preventDefault(); setError('');
    let url = authMode === 'login' ? 'login/' : authMode === 'registro' ? 'registro/' : 'cambiar-password/';
    try {
        const res = await fetch(`http://127.0.0.1:8000/api/${url}`, {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(authData)
        });
        const data = await res.json();
        if (res.ok) {
            if (authMode === 'login') {
                setUsuario({ id: data.user_id, username: data.username });
                setPuntuacionAcumulada(data.puntos);
                setCurrentStep(STEP_MODO); 
            } else {
                alert(data.mensaje || 'Operación exitosa');
                setAuthMode('login');
            }
        } else setError(data.error);
    } catch (err) { setError('Error de conexión'); }
  };

  const handleCerrarSesion = () => { setUsuario(null); setCurrentStep(STEP_LOGIN); };

  const actualizarPuntosGlobalesBD = (nuevosPuntos) => {
      setPuntuacionAcumulada(nuevosPuntos);
      if (usuario) {
          fetch('http://127.0.0.1:8000/api/actualizar-puntos/', {
              method: 'POST', headers: {'Content-Type': 'application/json'},
              body: JSON.stringify({ user_id: usuario.id, puntos: nuevosPuntos })
          });
      }
  };

  // --------------------------------------------------------------------------------
  // 2. LÓGICA DE SELECCIÓN Y GENERACIÓN ALEATORIA
  // --------------------------------------------------------------------------------
  const iniciarModo = async (tipo) => {
      setModoSeleccionado(tipo);
      await cargarSiguienteEjercicio(tipo);
  };

  const cargarSiguienteEjercicio = async (tipo) => {
      setCargandoEjercicio(true); 
      setEjercicioJuego(null);    
      setFaseClasificacion(1);
      setFeedbackClasificacion('');
      setError('');
      
      try {
          if (listaModelosDisponibles.length === 0) {
             const resModelos = await fetch('http://127.0.0.1:8000/api/lista-modelos/');
             if (resModelos.ok) {
                 const dataModelos = await resModelos.json();
                 setListaModelosDisponibles(dataModelos.modelos || []);
             }
          }

          const res = await fetch('http://127.0.0.1:8000/api/ejercicio-aleatorio/', {
              method: 'POST', headers: {'Content-Type': 'application/json'},
              body: JSON.stringify({ user_id: usuario.id, tipo: tipo })
          });
          const data = await res.json();
          
          if (data.status === 'exito') {
              setTimeout(() => {
                  setEjercicioJuego(data);
                  setCurrentStep(STEP_CLASIFICAR_JUEGO);
                  setCargandoEjercicio(false); 
              }, 300);
          } else if (data.status === 'fin') {
              // ACTUALIZACIÓN 3c: En lugar de alerta fea, vamos a la pantalla final
              setCurrentStep(STEP_FINAL);
              setCargandoEjercicio(false);
          } else {
              setError(data.error);
              setCargandoEjercicio(false);
          }
      } catch (err) { 
          setError('Error conectando al servidor');
          setCargandoEjercicio(false);
      }
  };

  // --------------------------------------------------------------------------------
  // 3. LÓGICA DE CLASIFICACIÓN (EL JUEGO)
  // --------------------------------------------------------------------------------
  const verificarClasificacion = (respuesta) => {
      const real = ejercicioJuego.caracteristicas;
      
      if (respuesta === 'UNA_VEZ') {
          if (real.incognita_una_vez) {
              avanzarAResolver();
          } else {
              setFeedbackClasificacion('Incorrecto. Fíjate bien si la X aparece solo una vez.');
          }
      } 
      else if (respuesta === 'NO_UNA_VEZ') {
          if (!real.incognita_una_vez) {
              setFaseClasificacion(2); 
              setFeedbackClasificacion('');
          } else {
              setFeedbackClasificacion('Incorrecto. La incógnita SÍ aparece una sola vez.');
          }
      }
      else {
          const esCorrecto = (
              respuesta.incognita_mas_de_una_vez === true &&
              respuesta.con_parentesis === real.con_parentesis &&
              respuesta.con_fracciones === real.con_fracciones
          );

          if (esCorrecto) {
              avanzarAResolver();
          } else {
              setFeedbackClasificacion('Clasificación incorrecta. Revisa las características.');
          }
      }
  };

  const avanzarAResolver = () => {
      setFeedbackClasificacion('¡Correcto! Ecuación localizada.');
      setTimeout(() => {
          setEcuacionActual(ejercicioJuego.ecuacion_str);
          resetResolverStates();
          handleSubmitResolucion(ejercicioJuego.ecuacion_str);
          setCurrentStep(STEP_RESOLVER);
      }, 1000);
  };

  // --------------------------------------------------------------------------------
  // 4. LÓGICA RESOLVER (CORE)
  // --------------------------------------------------------------------------------
  const resetResolverStates = () => {
    setError(''); setMensajeResultado(''); setPasosEntrenamiento([]); setSolucionEntrenamiento('');
    setModoPruebaActivo(false); setPuntosEjercicio(10); setPasosCompletosOcultos([]);
    setPasosReveladosCount(0); setMostrarSolucionFinal(false); setRespuestaEstudiante('');
  };

  const handleSubmitResolucion = async (ecuacionStr) => {
    try {
      const res = await fetch('http://127.0.0.1:8000/api/resolver/', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ ecuacion: ecuacionStr })
      });
      const data = await res.json();
      if (!res.ok) { setError(data.error); return; }

      if (data.fuente === 'Entrenamiento') {
        setPasosEntrenamiento(data.pasos_resolucion);
        setSolucionEntrenamiento(data.solucion_final); 
      } else {
        setModoPruebaActivo(true);
        setSolucionOculta(data.solucion_oculta);
        setSolucionFinalLatex(data.solucion_final_latex);
        setPasosCompletosOcultos(data.pasos_completos_ocultos);
      }
    } catch(err) { setError('Error conexión'); }
  };

  const completarEjercicioYContinuar = async () => {
      if (usuario) {
          await fetch('http://127.0.0.1:8000/api/marcar-completado/', {
              method: 'POST', headers: {'Content-Type': 'application/json'},
              body: JSON.stringify({ user_id: usuario.id, ejercicio_id: ejercicioJuego.id })
          });
      }
      cargarSiguienteEjercicio(modoSeleccionado);
  };

  const getReglasModelo = () => {
    const nombreModeloReal = ejercicioJuego && ejercicioJuego.modelo_id ? 
        listaModelosDisponibles.find(m => m.id === ejercicioJuego.modelo_id)?.nombre || "" : "";

    if (nombreModeloReal.includes("Modelo 1")) {
      return { costos: [3, 10, 0, 0], recuperacion: [1, 0, 0, 0] }; 
    }
    else if (nombreModeloReal.includes("Modelo 2")) {
      return { costos: [2, 4, 0, 0], recuperacion: [3, 1, 0, 0] };
    }
    else {
      return { costos: [1, 3, 5, 5], recuperacion: [1, 1, 0, 0] };
    }
  };

  const handleConsultarPaso = () => {
      if (pasosReveladosCount < pasosCompletosOcultos.length) {
          const siguientePasoIndex = pasosReveladosCount; 
          const reglas = getReglasModelo();
          
          const costo = reglas.costos[Math.min(siguientePasoIndex, reglas.costos.length - 1)];
          
          const nuevoCount = pasosReveladosCount + 1;
          const nuevosPuntosLocales = Math.max(0, puntosEjercicio - costo);
          
          setPasosReveladosCount(nuevoCount);
          setPuntosEjercicio(nuevosPuntosLocales);

          if (modoSeleccionado === 'PRUEBA') {
              actualizarPuntosGlobalesBD(puntuacionAcumulada - costo);
          }

          if (nuevoCount >= pasosCompletosOcultos.length) {
              setModoPruebaActivo(false);
              setMostrarSolucionFinal(true);
              setMensajeResultado("Todos los pasos revelados. No obtienes puntos extra.");
          }
      }
  };

  const handleCheckAnswer = (e) => {
      e.preventDefault(); setError('');
      
      const valUser = respuestaEstudiante.trim().toLowerCase();
      const valSys = solucionOculta.toString().trim().toLowerCase();
      const validosInfinitas = ["infinitas", "infinitas soluciones", "infinita", "todo numero real"];
      const validosSinSolucion = ["sin solución", "no tiene solución", "ninguna solución", "sin solucion", "no tiene solucion", "ninguna solucion"];

      let esCorrecto = false;
      if (validosInfinitas.some(v => valSys.includes(v))) { esCorrecto = validosInfinitas.includes(valUser); }
      else if (validosSinSolucion.some(v => valSys.includes(v))) { esCorrecto = validosSinSolucion.includes(valUser); }
      else { esCorrecto = (valUser === valSys); }

      if (esCorrecto) {
          const reglas = getReglasModelo();
          let puntosRecuperados = 0;

          if (pasosReveladosCount === 1) {
              puntosRecuperados = reglas.recuperacion[0] || 0;
          } else if (pasosReveladosCount === 2) {
              puntosRecuperados = reglas.recuperacion[1] || 0;
          }

          const totalGanado = puntosEjercicio + puntosRecuperados;
          
          if (modoSeleccionado === 'PRUEBA') {
              actualizarPuntosGlobalesBD(puntuacionAcumulada + totalGanado);
          }
          
          setMensajeResultado(`¡Correcto! Puntos: ${puntosEjercicio} + ${puntosRecuperados} (recuperados) = ${totalGanado}.`);
          setModoPruebaActivo(false);
          setMostrarSolucionFinal(true);
      } else {
          setPuntosEjercicio(prev => Math.max(0, prev - 1));
          
          if (modoSeleccionado === 'PRUEBA') {
              actualizarPuntosGlobalesBD(puntuacionAcumulada - 1);
          }

          setError('Incorrecto. Intenta de nuevo. (-1 punto)');
      }
  };

  // --------------------------------------------------------------------------------
  // VISTAS
  // --------------------------------------------------------------------------------

  // VISTA 1: LOGIN
  const renderLogin = () => (
      <div className="login-container" style={{marginTop:'50px', border:'1px solid #61dafb', padding:'30px', borderRadius:'10px'}}>
          <h2>{authMode==='login'?'Iniciar Sesión':authMode==='registro'?'Registro':'Cambiar Clave'}</h2>
          <form onSubmit={handleAuthSubmit} style={{display:'flex', flexDirection:'column', gap:'15px', width:'300px'}}>
              <input type="text" placeholder="Usuario" value={authData.username} onChange={e=>setAuthData({...authData, username:e.target.value})} style={{padding:'10px'}}/>
              <input type="password" placeholder="Contraseña" value={authData.password} onChange={e=>setAuthData({...authData, password:e.target.value})} style={{padding:'10px'}}/>
              {authMode==='cambiar' && <input type="password" placeholder="Nueva Clave" value={authData.new_password} onChange={e=>setAuthData({...authData, new_password:e.target.value})} style={{padding:'10px'}}/>}
              <button type="submit" style={{padding:'10px', background:'#61dafb', border:'none', fontWeight:'bold'}}>{authMode==='login'?'Entrar':'Enviar'}</button>
          </form>
          {error && <p style={{color:'red'}}>{error}</p>}
          
          <div style={{marginTop:'20px', display:'flex', flexDirection:'column', gap:'10px'}}>
              {authMode === 'login' ? (
                  <>
                    <button onClick={()=>setAuthMode('registro')} style={{padding:'8px', background:'transparent', border:'1px solid #61dafb', color:'#61dafb', cursor:'pointer'}}>Crear Usuario</button>
                    <button onClick={()=>setAuthMode('cambiar')} style={{padding:'8px', background:'transparent', border:'1px solid #fff', color:'#fff', cursor:'pointer'}}>Cambiar Contraseña</button>
                  </>
              ) : (
                  <button onClick={()=>setAuthMode('login')} style={{padding:'8px', background:'gray', border:'none', color:'#fff', cursor:'pointer'}}>Volver al Login</button>
              )}
          </div>
      </div>
  );

  // VISTA 2: SELECCIÓN MODO
  const renderModo = () => (
      <div style={{marginTop:'50px'}}>
          <h2>¿Entrenar o ponerte a prueba?</h2>
          <div style={{display:'flex', gap:'30px', justifyContent:'center', marginTop:'30px'}}>
              <button onClick={()=>iniciarModo('ENTRENAMIENTO')} style={{padding:'20px 40px', fontSize:'1.2rem', background:'#61dafb', border:'none', cursor:'pointer', borderRadius:'10px'}}>
                  ENTRENAMIENTO
              </button>
              <button onClick={()=>iniciarModo('PRUEBA')} style={{padding:'20px 40px', fontSize:'1.2rem', background:'#ff6b6b', color:'white', border:'none', cursor:'pointer', borderRadius:'10px'}}>
                  PRUEBA
              </button>
          </div>
      </div>
  );

  // VISTA 3: CLASIFICACIÓN (EL JUEGO)
  const renderClasificarJuego = () => (
      <div style={{width:'600px', margin:'auto'}}>
          <button onClick={() => setCurrentStep(STEP_MODO)} style={{float:'left', marginBottom:'10px'}}>Inicio</button>
          
          <h2>Clasifica la ecuación para encontrarla</h2>
          
          {cargandoEjercicio ? (
              <div style={{margin:'50px', fontSize:'1.2rem', color:'#61dafb'}}>Cargando nueva ecuación...</div>
          ) : (
              <div className="equation-box" style={{margin:'30px 0'}} key={`eq-${ejercicioJuego?.id}-${faseClasificacion}-${feedbackClasificacion}`}>
                  <p style={{fontSize:'1.5rem'}} dangerouslySetInnerHTML={{__html: ejercicioJuego?.ecuacion_str}} />
              </div>
          )}

          {feedbackClasificacion && <p style={{color: feedbackClasificacion.includes('Correcto') ? '#61dafb' : 'red', fontWeight:'bold'}}>{feedbackClasificacion}</p>}

          {!cargandoEjercicio && faseClasificacion === 1 && (
              <div style={{background:'transparent', border:'1px solid black', padding:'20px', borderRadius:'10px', color:'black'}}>
                  <h3>(1) ¿La incógnita aparece una sola vez?</h3>
                  <div style={{display:'flex', gap:'20px', justifyContent:'center', marginTop:'20px'}}>
                      <button onClick={()=>verificarClasificacion('UNA_VEZ')} style={{padding:'10px 30px', background:'#4caf50', color:'white', border:'none', cursor:'pointer'}}>Sí</button>
                      <button onClick={()=>verificarClasificacion('NO_UNA_VEZ')} style={{padding:'10px 30px', background:'#f44336', color:'white', border:'none', cursor:'pointer'}}>No</button>
                  </div>
              </div>
          )}

          {!cargandoEjercicio && faseClasificacion === 2 && (
              <div style={{background:'transparent', border:'1px solid black', padding:'20px', borderRadius:'10px', textAlign:'left', color:'black'}}>
                  <h3>Selecciona las características que ves:</h3>
                  <ClasificadorFase2 onVerificar={verificarClasificacion} />
              </div>
          )}
      </div>
  );

  // VISTA 4: RESOLVER
  const renderResolver = () => (
      <div style={{width:'600px', margin:'auto'}}>
          <button onClick={() => setCurrentStep(STEP_MODO)} style={{float:'left', marginBottom:'10px'}}>Inicio</button>
          
          <h2>Resolución</h2>
          <div className="equation-box"><p style={{fontSize:'1.5rem'}} dangerouslySetInnerHTML={{__html: ecuacionActual}}/></div>
          {error && <p style={{color:'red'}}>{error}</p>}
          {mensajeResultado && <p style={{color:'#61dafb'}}>{mensajeResultado}</p>}

          {solucionEntrenamiento && (
              <div style={{textAlign:'left', marginTop:'20px'}}>
                  <h3>Pasos (Entrenamiento):</h3>
                  <ListaPasos pasos={pasosEntrenamiento} solucionFinal={solucionEntrenamiento} />
                  <button onClick={()=>completarEjercicioYContinuar()} style={{marginTop:'30px', width:'100%', padding:'15px', background:'#61dafb', border:'none', fontWeight:'bold', cursor:'pointer'}}>
                      SIGUIENTE ECUACIÓN &rarr;
                  </button>
              </div>
          )}

          {(modoPruebaActivo || mostrarSolucionFinal) && (
              <div style={{marginTop:'20px', border:'1px solid #ccc', padding:'20px'}}>
                  <div style={{display:'flex', justifyContent:'space-between'}}>
                      <span>Puntos ejercicio: {puntosEjercicio}</span>
                  </div>
                  
                  <div style={{textAlign:'left'}}>
                      {pasosCompletosOcultos.slice(0, pasosReveladosCount).map((p, i) => (
                          <div key={i} className="step" style={{marginTop:'10px'}}>
                              <strong>Paso {p.paso || (i + 1)}:</strong> {p.descripcion}
                              <p dangerouslySetInnerHTML={{__html: p.ecuacion}}/>
                          </div>
                      ))}
                  </div>

                  {modoPruebaActivo && (
                      <div style={{marginTop:'20px'}}>
                          <button onClick={handleConsultarPaso} style={{marginRight:'10px', padding:'10px'}}>Consultar Paso</button>
                          
                          <form onSubmit={handleCheckAnswer} style={{marginTop:'10px'}}>
                              <input value={respuestaEstudiante} onChange={e=>setRespuestaEstudiante(e.target.value)} placeholder="Respuesta final" style={{padding:'10px'}}/>
                              <button type="submit" style={{padding:'10px', marginLeft:'10px'}}>Comprobar</button>
                          </form>
                      </div>
                  )}

                  {mostrarSolucionFinal && (
                      <div>
                          <div className="final" style={{marginTop:'20px'}}>Solución: <span dangerouslySetInnerHTML={{__html: solucionFinalLatex}}/></div>
                          <button onClick={()=>completarEjercicioYContinuar()} style={{marginTop:'20px', width:'100%', padding:'15px', background:'#61dafb', border:'none', fontWeight:'bold', cursor:'pointer'}}>
                              SIGUIENTE ECUACIÓN &rarr;
                          </button>
                      </div>
                  )}
              </div>
          )}
      </div>
  );

  // VISTA 5: PANTALLA FINAL (NUEVA VISTA)
  const renderPantallaFinal = () => {
      let mensajeFinal = "¡Has completado todos los ejercicios!";
      if (puntuacionAcumulada >= 250) {
          mensajeFinal = "Excelente, si te apetece puedes pasar a otro tipo de ecuaciones.";
      } else if (puntuacionAcumulada >= 150) {
          mensajeFinal = "Necesitas un poco más de entreno.";
      } else {
          mensajeFinal = "Vuelve a realizar todos los ejercicios de prueba.";
      }

      return (
          <div style={{marginTop:'50px', border:'1px solid #61dafb', padding:'30px', borderRadius:'10px', backgroundColor:'#f9f9f9'}}>
              <h2 style={{color:'#222'}}>¡Felicidades!</h2>
              <p style={{fontSize:'1.2rem', color:'#555'}}>{mensajeFinal}</p>
              <div style={{fontSize:'3rem', color:'#61dafb', fontWeight:'bold', margin:'20px 0'}}>
                  {puntuacionAcumulada} pts
              </div>

              {/* TABLA DE RANKING (3a) */}
              <div style={{marginTop:'30px'}}>
                  <h3 style={{color:'#333'}}>Top 10 Usuarios</h3>
                  <table style={{width:'100%', maxWidth:'400px', margin:'auto', borderCollapse:'collapse'}}>
                      <thead>
                          <tr style={{background:'#eee'}}>
                              <th style={{padding:'10px', textAlign:'left'}}>Usuario</th>
                              <th style={{padding:'10px', textAlign:'right'}}>Puntos</th>
                          </tr>
                      </thead>
                      <tbody>
                          {rankingData.map((r, i) => (
                              <tr key={i} style={{borderBottom:'1px solid #ddd'}}>
                                  <td style={{padding:'10px', textAlign:'left'}}>{r.username}</td>
                                  <td style={{padding:'10px', textAlign:'right'}}>{r.puntos}</td>
                              </tr>
                          ))}
                      </tbody>
                  </table>
              </div>

              <button onClick={() => setCurrentStep(STEP_MODO)} style={{marginTop:'30px', padding:'15px 30px', background:'#61dafb', border:'none', fontWeight:'bold', cursor:'pointer', fontSize:'1rem'}}>
                  Volver al Menú
              </button>
          </div>
      );
  };

  return (
    <div className="App">
      {usuario && (
          <div style={{position:'fixed', top:10, right:10, background:'transparent', padding:'10px', border:'1px solid #61dafb', color:'black'}}>
              <div>User: {usuario.username}</div>
              {/* CORRECCIÓN 1a: Tamaño fuente puntuación */}
              <div style={{color:'#61dafb', fontWeight:'bold', fontSize:'2.5rem'}}>{puntuacionAcumulada} pts</div>
              <button onClick={handleCerrarSesion} style={{color:'red', marginTop:'5px'}}>Salir</button>
          </div>
      )}
      
      <main className="App-header">
        {currentStep === STEP_LOGIN && renderLogin()}
        {currentStep === STEP_MODO && renderModo()}
        {currentStep === STEP_CLASIFICAR_JUEGO && renderClasificarJuego()}
        {currentStep === STEP_RESOLVER && renderResolver()}
        {currentStep === STEP_FINAL && renderPantallaFinal()}
      </main>
    </div>
  );
}

const ClasificadorFase2 = ({ onVerificar }) => {
    const [opts, setOpts] = useState({ incognita_mas_de_una_vez: false, con_parentesis: false, con_fracciones: false });
    return (
        <div>
            <label style={{display:'block', margin:'10px 0'}}>
                <input type="checkbox" checked={opts.incognita_mas_de_una_vez} onChange={e=>setOpts({...opts, incognita_mas_de_una_vez:e.target.checked})}/>
                La incógnita aparece más de una vez
            </label>
            <label style={{display:'block', margin:'10px 0'}}>
                <input type="checkbox" checked={opts.con_parentesis} onChange={e=>setOpts({...opts, con_parentesis:e.target.checked})}/>
                Hay paréntesis
            </label>
            <label style={{display:'block', margin:'10px 0'}}>
                <input type="checkbox" checked={opts.con_fracciones} onChange={e=>setOpts({...opts, con_fracciones:e.target.checked})}/>
                Hay fracciones
            </label>
            <button onClick={()=>onVerificar(opts)} style={{marginTop:'20px', padding:'10px 20px'}}>Localizar Ecuación</button>
        </div>
    );
};

const ListaPasos = ({ pasos, solucionFinal }) => {
  useEffect(() => { setTimeout(runMathJax, 100); }, [pasos]);
  return (
    <div>
      {pasos.map((p, i) => (
        <div key={i} className="step">
            <strong>Paso {p.paso || (i + 1)}:</strong> {p.descripcion}
            <p dangerouslySetInnerHTML={{__html: p.ecuacion}} />
        </div>
      ))}
      <div className="final">Solución: <span dangerouslySetInnerHTML={{__html: solucionFinal}} /></div>
    </div>
  );
};

export default App;