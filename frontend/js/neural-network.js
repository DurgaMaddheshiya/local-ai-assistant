/**
 * Neural Network Animation
 * Animated nodes with connecting lines
 */

class NeuralNetwork {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        if (!this.canvas) return;
        
        this.ctx = this.canvas.getContext('2d');
        this.nodes = [];
        this.nodeCount = 50;
        this.maxDistance = 150;
        this.nodeSpeed = 0.3;
        
        this.colors = {
            node: 'rgba(245, 158, 11, 0.8)', // Amber
            line: 'rgba(245, 158, 11, 0.2)',
            nodeGlow: 'rgba(245, 158, 11, 0.4)'
        };
        
        this.init();
        this.animate();
        
        // Resize handler
        window.addEventListener('resize', () => this.init());
    }
    
    init() {
        // Set canvas size
        this.canvas.width = window.innerWidth;
        this.canvas.height = window.innerHeight;
        
        // Create nodes
        this.nodes = [];
        for (let i = 0; i < this.nodeCount; i++) {
            this.nodes.push({
                x: Math.random() * this.canvas.width,
                y: Math.random() * this.canvas.height,
                vx: (Math.random() - 0.5) * this.nodeSpeed,
                vy: (Math.random() - 0.5) * this.nodeSpeed,
                radius: Math.random() * 2 + 1
            });
        }
    }
    
    drawNode(node) {
        // Glow effect
        this.ctx.beginPath();
        this.ctx.arc(node.x, node.y, node.radius + 3, 0, Math.PI * 2);
        this.ctx.fillStyle = this.colors.nodeGlow;
        this.ctx.fill();
        
        // Node
        this.ctx.beginPath();
        this.ctx.arc(node.x, node.y, node.radius, 0, Math.PI * 2);
        this.ctx.fillStyle = this.colors.node;
        this.ctx.fill();
    }
    
    drawLine(node1, node2, distance) {
        const opacity = 1 - (distance / this.maxDistance);
        this.ctx.beginPath();
        this.ctx.moveTo(node1.x, node1.y);
        this.ctx.lineTo(node2.x, node2.y);
        this.ctx.strokeStyle = `rgba(245, 158, 11, ${opacity * 0.2})`;
        this.ctx.lineWidth = 0.5;
        this.ctx.stroke();
    }
    
    updateNode(node) {
        // Update position
        node.x += node.vx;
        node.y += node.vy;
        
        // Bounce off edges
        if (node.x < 0 || node.x > this.canvas.width) {
            node.vx *= -1;
            node.x = Math.max(0, Math.min(this.canvas.width, node.x));
        }
        if (node.y < 0 || node.y > this.canvas.height) {
            node.vy *= -1;
            node.y = Math.max(0, Math.min(this.canvas.height, node.y));
        }
    }
    
    animate() {
        // Clear canvas
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Update and draw nodes
        this.nodes.forEach(node => {
            this.updateNode(node);
        });
        
        // Draw connections
        for (let i = 0; i < this.nodes.length; i++) {
            for (let j = i + 1; j < this.nodes.length; j++) {
                const dx = this.nodes[i].x - this.nodes[j].x;
                const dy = this.nodes[i].y - this.nodes[j].y;
                const distance = Math.sqrt(dx * dx + dy * dy);
                
                if (distance < this.maxDistance) {
                    this.drawLine(this.nodes[i], this.nodes[j], distance);
                }
            }
        }
        
        // Draw nodes on top
        this.nodes.forEach(node => {
            this.drawNode(node);
        });
        
        // Continue animation
        requestAnimationFrame(() => this.animate());
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new NeuralNetwork('neural-canvas');
});
