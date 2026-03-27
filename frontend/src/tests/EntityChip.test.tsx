/**
 * Unit tests for EntityChip component
 */
import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import EntityChip from '../components/ChatInterface/EntityChip'

describe('EntityChip', () => {
  it('renders entity ID', () => {
    render(<EntityChip entityId="CUST-001" onClick={() => {}} />)
    expect(screen.getByText('CUST-001')).toBeInTheDocument()
  })

  it('calls onClick when clicked', () => {
    const mockOnClick = vi.fn()
    render(<EntityChip entityId="CUST-001" onClick={mockOnClick} />)

    const chip = screen.getByText('CUST-001')
    fireEvent.click(chip)

    expect(mockOnClick).toHaveBeenCalledWith('CUST-001')
  })

  it('applies correct color for Customer', () => {
    const { container } = render(
      <EntityChip entityId="CUST-001" onClick={() => {}} />
    )

    const chip = container.querySelector('button')
    expect(chip).toHaveClass('bg-blue-100')
  })

  it('applies correct color for Product', () => {
    const { container } = render(
      <EntityChip entityId="PROD-001" onClick={() => {}} />
    )

    const chip = container.querySelector('button')
    expect(chip).toHaveClass('bg-green-100')
  })

  it('applies correct color for Order', () => {
    const { container } = render(
      <EntityChip entityId="ORD-001" onClick={() => {}} />
    )

    const chip = container.querySelector('button')
    expect(chip).toHaveClass('bg-orange-100')
  })

  it('handles numeric customer IDs', () => {
    const { container } = render(
      <EntityChip entityId="310000108" onClick={() => {}} />
    )

    expect(screen.getByText('310000108')).toBeInTheDocument()
    const chip = container.querySelector('button')
    expect(chip).toHaveClass('bg-blue-100') // Should be treated as Customer
  })
})
