import { useCounterStore } from './counterStore';

function App() {
  // Store se cheezein nikalna
  const { count, increment, decrement } = useCounterStore();

  return (
    <div style={{ textAlign: 'center', marginTop: '50px' }}>
      <h1>Zustand Counter</h1>
      <h2>{count}</h2>
      <button onClick={increment}>Plus +</button>
      <button onClick={decrement} style={{ marginLeft: '10px' }}>Minus -</button>
    </div>
  );
}

export default App;