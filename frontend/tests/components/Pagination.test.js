import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import Pagination from '@/components/common/Pagination.vue'

describe('Pagination Component', () => {
  it('should render correctly', () => {
    const wrapper = mount(Pagination, {
      props: {
        page: 1,
        pageSize: 20,
        total: 100
      }
    })

    expect(wrapper.find('.pagination').exists()).toBe(true)
  })

  it('should receive correct props', () => {
    const wrapper = mount(Pagination, {
      props: {
        page: 1,
        pageSize: 20,
        total: 100
      }
    })

    expect(wrapper.props('page')).toBe(1)
    expect(wrapper.props('pageSize')).toBe(20)
    expect(wrapper.props('total')).toBe(100)
  })

  it('should update current page when props change', async () => {
    const wrapper = mount(Pagination, {
      props: {
        page: 1,
        pageSize: 20,
        total: 100
      }
    })

    await wrapper.setProps({ page: 2 })

    expect(wrapper.props('page')).toBe(2)
  })
})
