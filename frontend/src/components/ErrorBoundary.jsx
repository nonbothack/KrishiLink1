import { Component } from 'react';
export default class ErrorBoundary extends Component {
 state={failed:false};
 static getDerivedStateFromError(){return {failed:true};}
 componentDidUpdate(previous){if(previous.resetKey!==this.props.resetKey&&this.state.failed)this.setState({failed:false});}
 render(){if(this.state.failed)return <div className="data-state" role="alert"><h1>{this.props.title}</h1><button className="button" onClick={()=>this.setState({failed:false})}>{this.props.retry}</button><a className="text-link" href="/">{this.props.home}</a></div>;return this.props.children;}
}
