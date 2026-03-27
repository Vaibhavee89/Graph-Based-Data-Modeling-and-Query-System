/**
 * Unit tests for FilterPanel component
 */
import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import FilterPanel, { GraphFilters } from '../components/GraphCanvas/FilterPanel'

describe('FilterPanel', () => {
  const availableNodeTypes = ['Customer', 'Product', 'Order']
  const availableEdgeTypes = ['PLACED', 'CONTAINS', 'GENERATED']

  const defaultFilters: GraphFilters = {
    nodeTypes: new Set(['Customer', 'Product', 'Order']),
    edgeTypes: new Set(['PLACED', 'CONTAINS', 'GENERATED']),
  }

  const mockOnFiltersChange = vi.fn()
  const mockOnReset = vi.fn()

  it('renders filter button', () => {
    render(
      <FilterPanel
        filters={defaultFilters}
        availableNodeTypes={availableNodeTypes}
        availableEdgeTypes={availableEdgeTypes}
        onFiltersChange={mockOnFiltersChange}
        onReset={mockOnReset}
      />
    )

    expect(screen.getByText('Filters')).toBeInTheDocument()
  })

  it('expands when clicked', () => {
    render(
      <FilterPanel
        filters={defaultFilters}
        availableNodeTypes={availableNodeTypes}
        availableEdgeTypes={availableEdgeTypes}
        onFiltersChange={mockOnFiltersChange}
        onReset={mockOnReset}
      />
    )

    const filterButton = screen.getByText('Filters')
    fireEvent.click(filterButton)

    expect(screen.getByText('Node Types')).toBeInTheDocument()
    expect(screen.getByText('Edge Types')).toBeInTheDocument()
  })

  it('shows node type checkboxes', () => {
    render(
      <FilterPanel
        filters={defaultFilters}
        availableNodeTypes={availableNodeTypes}
        availableEdgeTypes={availableEdgeTypes}
        onFiltersChange={mockOnFiltersChange}
        onReset={mockOnReset}
      />
    )

    fireEvent.click(screen.getByText('Filters'))

    availableNodeTypes.forEach((type) => {
      expect(screen.getByText(type)).toBeInTheDocument()
    })
  })

  it('calls onFiltersChange when toggling node type', () => {
    render(
      <FilterPanel
        filters={defaultFilters}
        availableNodeTypes={availableNodeTypes}
        availableEdgeTypes={availableEdgeTypes}
        onFiltersChange={mockOnFiltersChange}
        onReset={mockOnReset}
      />
    )

    fireEvent.click(screen.getByText('Filters'))

    const customerCheckbox = screen.getByRole('checkbox', { name: /Customer/i })
    fireEvent.click(customerCheckbox)

    expect(mockOnFiltersChange).toHaveBeenCalled()
  })

  it('shows active filter count badge', () => {
    const partialFilters: GraphFilters = {
      nodeTypes: new Set(['Customer']), // Only 1 of 3
      edgeTypes: new Set(['PLACED', 'CONTAINS', 'GENERATED']),
    }

    render(
      <FilterPanel
        filters={partialFilters}
        availableNodeTypes={availableNodeTypes}
        availableEdgeTypes={availableEdgeTypes}
        onFiltersChange={mockOnFiltersChange}
        onReset={mockOnReset}
      />
    )

    // Should show badge with count 1 (node types filtered)
    expect(screen.getByText('1')).toBeInTheDocument()
  })

  it('calls onReset when Reset All clicked', () => {
    render(
      <FilterPanel
        filters={defaultFilters}
        availableNodeTypes={availableNodeTypes}
        availableEdgeTypes={availableEdgeTypes}
        onFiltersChange={mockOnFiltersChange}
        onReset={mockOnReset}
      />
    )

    fireEvent.click(screen.getByText('Filters'))
    const resetButton = screen.getByText('Reset All')
    fireEvent.click(resetButton)

    expect(mockOnReset).toHaveBeenCalled()
  })
})
