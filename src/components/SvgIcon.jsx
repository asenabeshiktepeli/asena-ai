function SvgIcon({ href, className = 'button-icon' }) {
  return (
    <svg className={className} role="presentation" aria-hidden="true">
      <use href={href}></use>
    </svg>
  )
}

export default SvgIcon
