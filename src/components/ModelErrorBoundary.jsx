import { Component } from 'react';

/**
 * If graft_environment.glb is missing or fails to parse, render the fallback
 * (the procedural placeholder scene) instead of crashing the canvas.
 */
export default class ModelErrorBoundary extends Component {
  state = { failed: false };

  static getDerivedStateFromError() {
    return { failed: true };
  }

  componentDidCatch(error) {
    console.warn('[GraftModel] Could not load model, using placeholder scene.', error);
    this.props.onError?.(error);
  }

  render() {
    return this.state.failed ? this.props.fallback : this.props.children;
  }
}
